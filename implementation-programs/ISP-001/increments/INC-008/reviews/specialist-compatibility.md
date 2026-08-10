# INC-008 Compatibility Review

Reviewer: controller self-review; non-independent; reduced assurance.

Reviewed candidate: `de7dc8f1aa8c52acdbd80c3d8670b0af44b481dd3d0091df0db83c54ed3964c6`.

The production repair changes only rollover behavior for the previously rejected both-present, regular, non-symlink, byte-exact navigation case. Create-new behavior remains intact; mixed, changed, unsafe, and unsupported records fail closed. Existing persisted schemas and public names are unchanged. Current schemas pass and unsupported versions return explicit issues; no older-schema compatibility is claimed where no older fixture exists.

No material compatibility finding was identified.
