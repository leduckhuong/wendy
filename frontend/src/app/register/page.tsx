"use client";

import { useRouter } from "next/navigation";
import { Toaster } from "sonner";
import userService from "@/services/user";
import { delay, notify } from "@/libs/utils";
import { FormEvent } from "react";

export default function Register() {
  const router = useRouter();

  const handleSubmit = async function (event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);

    const usernameValue = formData.get("username");
    const passwordValue = formData.get("password");
    const confirmPasswordValue = formData.get("confirmPassword");

    if (
      typeof usernameValue !== "string" ||
      typeof passwordValue !== "string" ||
      typeof confirmPasswordValue !== "string"
    ) {
      notify.error("Invalid input types");
      return;
    }

    const username = usernameValue.trim();
    const password = passwordValue;
    const confirmPassword = confirmPasswordValue;

    if (!username || !password || !confirmPassword) {
      notify.error("All fields are required");
      return;
    }

    if (password !== confirmPassword) {
      notify.error("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      notify.error("Password must be at least 8 characters long");
      return;
    }

    try {
      const response = await userService.register(username, password);
      if (response.status === 200) {
        notify.success("Registration successful! Please login.");
        await delay(500);
        router.push("/login");
      }
    } catch (error: any) {
      console.error("Registration error:", error);
      notify.error(error.response?.data?.message || "Registration failed");
    }
  };

  return (
    <>
      <div className="h-screen backdrop-blur flex justify-center items-center">
        <Toaster />
        <div>
          <form
            className="min-w-[24rem] mx-auto bg-slate-800 text-white dark:bg-white dark:text-slate-600 py-16 px-4 rounded-md"
            onSubmit={handleSubmit}
          >
            <h1 className="text-center text-3xl font-semibold">Register</h1>
            <div className="mt-2 flex flex-col">
              <label htmlFor="username" className="text-base font-semibold">
                Username
              </label>
              <input
                type="text"
                name="username"
                className="my-1 p-2 border border-slate-300 focus:outline-1 rounded-md"
                placeholder="Enter your username..."
                autoFocus
                required
              />
            </div>
            <div className="mt-2 flex flex-col">
              <label htmlFor="password" className="text-base font-semibold">
                Password
              </label>
              <input
                type="password"
                name="password"
                className="my-1 p-2 border border-slate-300 focus:outline-1 rounded-md"
                placeholder="Enter your password..."
                required
              />
            </div>
            <div className="mt-2 flex flex-col">
              <label htmlFor="confirmPassword" className="text-base font-semibold">
                Confirm Password
              </label>
              <input
                type="password"
                name="confirmPassword"
                className="my-1 p-2 border border-slate-300 focus:outline-1 rounded-md"
                placeholder="Confirm your password..."
                required
              />
            </div>
            <div className="mt-2 flex flex-col">
              <input
                type="submit"
                className="my-1 p-2 bg-cyan-600 text-slate-400 rounded-md cursor-pointer hover:text-white hover:bg-cyan-800"
                value="Register"
              />
            </div>
            <div className="text-center mt-4">
              <a href="/login" className="text-cyan-400 hover:text-cyan-300">
                Already have an account? Login here
              </a>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
