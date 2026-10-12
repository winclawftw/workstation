from .contracts import ApprovalDecision


class PolicyEngine:
    dangerous_actions = frozenset({"delete", "overwrite", "publish", "credentials", "system"})

    def evaluate(self, action: str) -> ApprovalDecision:
        if action in self.dangerous_actions:
            return ApprovalDecision(False, True, f"approval required for {action}")
        return ApprovalDecision(True, False, "allowed by default read-only policy")


class ApprovalService:
    def request(self, action: str, reason: str = "") -> ApprovalDecision:
        return ApprovalDecision(False, True, reason or f"approval required for {action}")
