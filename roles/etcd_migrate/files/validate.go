/*
Copyright 2016 The Kubernetes Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"reflect"
	"time"

	"github.com/coreos/etcd/client"
	"github.com/coreos/etcd/clientv3"
	"github.com/coreos/etcd/pkg/transport"
	"github.com/golang/glog"
	"golang.org/x/net/context"
)

type etcdFlags struct {
	etcdAddress *string
	certFile    *string
	keyFile     *string
	caFile      *string
}

func generateV2ClientConfig(flags *etcdFlags) (client.Client, error) {
	if *(flags.etcdAddress) == "" {
		return nil, fmt.Errorf("--etcd-address flag is required")
	}

	tls := transport.TLSInfo{
		CAFile:   *(flags.caFile),
		CertFile: *(flags.certFile),
		KeyFile:  *(flags.keyFile),
	}

	tr, err := transport.NewTransport(tls, 30*time.Second)
	if err != nil {
		return nil, err
	}

	cfg := client.Config{
		Transport:               tr,
		Endpoints:               []string{*(flags.etcdAddress)},
		HeaderTimeoutPerRequest: 30 * time.Second,
	}

	return client.New(cfg)
}

func generateV3ClientConfig(flags *etcdFlags) (*clientv3.Config, error) {
	if *(flags.etcdAddress) == "" {
		return nil, fmt.Errorf("--etcd-address flag is required")
	}

	c := &clientv3.Config{
		Endpoints: []string{*(flags.etcdAddress)},
	}

	var cfgtls *transport.TLSInfo
	tlsinfo := transport.TLSInfo{}
	if *(flags.certFile) != "" {
		tlsinfo.CertFile = *(flags.certFile)
		cfgtls = &tlsinfo
	}

	if *(flags.keyFile) != "" {
		tlsinfo.KeyFile = *(flags.keyFile)
		cfgtls = &tlsinfo
	}

	if *(flags.caFile) != "" {
		tlsinfo.CAFile = *(flags.caFile)
		cfgtls = &tlsinfo
	}

	if cfgtls != nil {
		clientTLS, err := cfgtls.ClientConfig()
		if err != nil {
			return nil, fmt.Errorf("Error while creating etcd client: %v", err)
		}
		c.TLS = clientTLS
	}
	return c, nil
}

func getV2Entry(keysAPI client.KeysAPI, key string) (*client.Response, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	resp, err := keysAPI.Get(ctx, key, &client.GetOptions{Sort: true, Quorum: true})
	cancel()
	return resp, err
}

func getV3Entry(c *clientv3.Client, key string) (*clientv3.GetResponse, error) {
	return c.KV.Get(context.Background(), key, clientv3.WithPrefix())
}

func getLeafKeys(nodes client.Nodes) []string {
	leaves := make([]string, 0, 0)
	for _, node := range nodes {
		if node.Dir {
			leaves = append(leaves, getLeafKeys(node.Nodes)...)
			continue
		}
		leaves = append(leaves, node.Key)
	}
	return leaves
}

func getV2Keys(keysAPI client.KeysAPI) ([]string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	lsresp, err := keysAPI.Get(ctx, "", &client.GetOptions{Sort: true, Quorum: true, Recursive: true})
	cancel()
	if err != nil {
		return nil, err
	}

	return getLeafKeys(lsresp.Node.Nodes), nil
}

// Picked from https://gist.github.com/turtlemonvh/e4f7404e28387fadb8ad275a99596f67
func AreEqualJSON(s1, s2 string) (bool, error) {
	var o1 interface{}
	var o2 interface{}

	var err error
	err = json.Unmarshal([]byte(s1), &o1)
	if err != nil {
		return false, fmt.Errorf("Error mashalling string 1 :: %s", err.Error())
	}
	err = json.Unmarshal([]byte(s2), &o2)
	if err != nil {
		return false, fmt.Errorf("Error mashalling string 2 :: %s", err.Error())
	}

	return reflect.DeepEqual(o1, o2), nil
}

func main() {
	flags := &etcdFlags{
		etcdAddress: flag.String("etcd-address", "", "Etcd address"),
		certFile:    flag.String("cert", "", "identify secure client using this TLS certificate file"),
		keyFile:     flag.String("key", "", "identify secure client using this TLS key file"),
		caFile:      flag.String("cacert", "", "verify certificates of TLS-enabled secure servers using this CA bundle"),
	}

	flag.Parse()

	v2ClientConfig, err := generateV2ClientConfig(flags)
	if err != nil {
		glog.Fatal(err)
	}

	keysAPI := client.NewKeysAPI(v2ClientConfig)

	v3ClientConfig, err := generateV3ClientConfig(flags)
	if err != nil {
		glog.Fatal(err)
	}

	v3Client, err := clientv3.New(*v3ClientConfig)
	if err != nil {
		glog.Fatal(err)
	}

	// Get all keys
	keys, err := getV2Keys(keysAPI)
	if err != nil {
		glog.Fatal(err)
	}

	total := len(keys)
	for i, key := range keys {
		v2resp, err := getV2Entry(keysAPI, key)
		if err != nil {
			glog.Fatal(err)
		}
		v3resp, err := getV3Entry(v3Client, key)
		if err != nil {
			glog.Fatal(err)
		}

		v2value := v2resp.Node.Value
		v3value := string(v3resp.Kvs[0].Value)

		ok, err := AreEqualJSON(v2value, v3value)
		if err != nil {
			glog.Fatal(err)
		}

		if !ok {
			glog.Fatal("Key %v has different value in v2 data than in v3 data:\nv2data: %v\nv3data: %v\n\n", v2value, v3value)
		} else {
			glog.Infof("OK: (%v/%v) Key %v\n", i+1, total, key)
		}
	}
}
