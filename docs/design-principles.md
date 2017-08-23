### Arch principles

This is a high-level document that references various design aspects we discussed
on our architecture meetings.

* [Role decomposition](proposals/role_decomposition.md):
roles that are very large and encompass a lot of different components should be
decomposed into smaller roles to decrease amount of logic required within the role,
to reduce complex conditionals, and decrease the learning curve for the role

* [Entry-point based roles](proposals/role-entry-points.md):
every role needs to have a well-defined API so a role caller communicates
only througth accepted set of role variables, thus making a role closed,
independent of surrounding system, more flexible and practically modular

* [Role dependency orchestration](proposals/role_dependency_orchestration.md):
minimize role dependencies in favor of role modularity and re-usability
by replacing a role invocation with a sequence of role invocations and its
dependencies, orchestrating dependencies on a play level

* [Action based roles](proposals/action_based_roles.md):
some roles may provide a set of actions that share common resources (e.g.
configuration files, templates, handlers), creating a role for each action
would result in a duplication of resources which we are trying to avoid

* TODO: **Role inclusion**:
the `include_role` keyword proves to be preferred over `role` as it removes
concept of `pre_tasks`, `roles`, `tasks` and `post_tasks`, thus aligning entire
play tasks space into a single sequence of tasks
