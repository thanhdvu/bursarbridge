import { NextResponse, type NextRequest } from "next/server";
import { surfaceOf } from "@/i18n/config";

/** Tags each request with its surface so the locale (per persona surface) resolves on the server. */
export function proxy(request: NextRequest) {
  const headers = new Headers(request.headers);
  headers.set("x-bb-surface", surfaceOf(request.nextUrl.pathname));
  return NextResponse.next({ request: { headers } });
}

export const config = {
  // Skip framework files, the API proxy and anything with a file extension.
  matcher: ["/((?!_next|api|bbapi|samples|favicon|opengraph-image|.*\\..*).*)"],
};
