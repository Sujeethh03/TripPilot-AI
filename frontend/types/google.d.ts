/** Minimal typing for the Google Identity Services (GIS) client we load at
 * runtime for Sign-In. Only the surface we actually use. */
interface GoogleCredentialResponse {
  credential: string; // the ID token (JWT) we POST to /auth/google
}

interface GoogleIdConfig {
  client_id: string;
  callback: (response: GoogleCredentialResponse) => void;
}

interface GoogleButtonOptions {
  type?: "standard" | "icon";
  theme?: "outline" | "filled_blue" | "filled_black";
  size?: "large" | "medium" | "small";
  text?: "signin_with" | "signup_with" | "continue_with";
  width?: number;
}

interface GoogleAccountsId {
  initialize: (config: GoogleIdConfig) => void;
  renderButton: (parent: HTMLElement, options: GoogleButtonOptions) => void;
}

interface Window {
  google?: { accounts: { id: GoogleAccountsId } };
}
