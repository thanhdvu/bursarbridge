import type { Approval, User } from "@/lib/api/types";

/** Who signs: the API may omit approverId; fall back to the documented rule (refund claims: student, everything else: parent). */
export function isMine(a: Approval, user: User | undefined) {
  if (!user) return false;
  if (a.approverId) return a.approverId === user.id;
  if (a.status === "cooling_off") return user.role === "cosigner" || user.role === "parent";
  return a.action === "refund_claim" ? user.role === "student" : user.role === "parent";
}
