"""
AuditService — source file where spy vs mock distinction matters.

audit_action() delegates to a real in-process formatter before calling
the external audit log writer. Tests need to:
  a) verify the external writer is called with the formatted string (mock)
  b) also confirm the formatter runs correctly and its output is used (spy candidate)
"""


class AuditService:
    def __init__(self, audit_writer):
        self._writer = audit_writer

    def audit_action(self, user_id: str, action: str, resource: str) -> None:
        """Format and persist an audit log entry.

        The formatted entry is passed to the audit_writer. The formatter
        is internal to this class — it is not injected.
        """
        entry = self._format_entry(user_id, action, resource)
        self._writer.write(entry)

    def _format_entry(self, user_id: str, action: str, resource: str) -> str:
        return f"[AUDIT] user={user_id} action={action} resource={resource}"
