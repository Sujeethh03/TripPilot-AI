/** Client-side form schemas (React Hook Form + Zod). Mirror the backend's
 * auth validation (password >= 8) so errors show before a round-trip. */
import { z } from "zod";

export const loginFormSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

export const registerFormSchema = z.object({
  name: z.string().optional(),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "At least 8 characters"),
});

export type LoginForm = z.infer<typeof loginFormSchema>;
export type RegisterForm = z.infer<typeof registerFormSchema>;

export const newTripFormSchema = z.object({
  destination: z.string().min(1, "Where are you going?"),
  title: z.string().optional(),
  origin: z.string().optional(),
  transport_mode: z.enum(["driving", "transit"]).optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  // The input converts "" → undefined via setValueAs (see NewTripDialog), so
  // this stays a plain optional number and RHF's input/output types match.
  budget_inr: z.number().int().positive("Enter a positive amount").optional(),
});

export type NewTripForm = z.infer<typeof newTripFormSchema>;
