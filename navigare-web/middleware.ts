import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextResponse as NR } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = [
  "/login",
  "/signup",
  "/api/proxy",
  "/api",
];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some(
    (p) => pathname === p || pathname.startsWith(p + "/") || pathname.startsWith(p)
  );
}

export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Allow public paths and static assets
  if (isPublicPath(pathname) || pathname.startsWith("/_next") || pathname === "/favicon.ico") {
    return NextResponse.next();
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  const authDisabled = process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

  // Skip auth if Supabase is not configured
  if (authDisabled || !supabaseUrl || !supabaseAnonKey) {
    return NextResponse.next();
  }

  let supabaseResponse = NextResponse.next({ request });
  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      get(key: string) {
        return request.cookies.get(key)?.value ?? null;
      },
      set(key: string, value: string, options: CookieOptions) {
        request.cookies.set(key, value);
        supabaseResponse = NextResponse.next({ request });
        supabaseResponse.cookies.set(key, value, options);
      },
      remove(key: string, options: CookieOptions) {
        request.cookies.set(key, "");
        supabaseResponse = NextResponse.next({ request });
        supabaseResponse.cookies.set(key, "", { ...options, maxAge: 0 });
      },
    },
  });

  const { data: { session } } = await supabase.auth.getSession();

  // Protect /dashboard routes — redirect to login if no session
  if (!session && pathname.startsWith("/dashboard")) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/login";
    redirectUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  return supabaseResponse;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
