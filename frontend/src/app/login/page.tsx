"use client";

import { useRouter } from "next/navigation";

import { Toaster } from "sonner";

import userService from "@/services/user";
import { delay, notify } from "@/libs/utils";

import { FormEvent } from "react";
import { AxiosResponse } from "axios";

export default function Login() {
  const router = useRouter();

  const handleSubmit = async function (event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);

    const usernameValue = formData.get("username");
    const passwordValue = formData.get("password");

    if (
      typeof usernameValue !== "string" ||
      typeof passwordValue !== "string"
    ) {
      console.error("Username or password are invalid");
      return;
    }

    const username = usernameValue;
    const password = passwordValue;

    const response: AxiosResponse = await userService.getToken(
      username,
      password
    );
    if (response.status == 200) {
      notify.success("Login success!");
      await delay(500);
      router.push("/");
    } else {
      return;
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
            <h1 className="text-center text-3xl font-semibold">Login</h1>
            <div className="mt-2 flex flex-col">
              <label htmlFor="" className="text-base font-semibold">
                Username
              </label>
              <input
                type="text"
                name="username"
                className="my-1 p-2 border border-slate-300 focus:outline-1 rounded-md"
                placeholder="Enter your username..."
                autoFocus
              />
              <div className="form__message"></div>
            </div>
            <div className="mt-2 flex flex-col">
              <label htmlFor="" className="text-base font-semibold">
                Password
              </label>
              <input
                type="password"
                name="password"
                className="my-1 p-2 border border-slate-300 focus:outline-1 rounded-md"
                placeholder="*****"
              />
              <div className="form__message"></div>
            </div>
            <div className="mt-2 flex flex-col">
              <input
                type="submit"
                className="my-1 p-2 bg-cyan-600 text-slate-400 rounded-md cursor-pointer hover:text-white hover:bg-cyan-800"
                value="Submit"
              />
            </div>
            <a href="/forgot" className="block mt-4 italic"></a>
            <a href="/register" className="block mt-4 text-center"></a>
            <p className="text-center text-slate-400">or</p>
            <ul className="flex justify-center items-center">
              <li className="w-16 h-16 flex justify-center items-center text-3xl text-sky-600 cursor-pointer opacity-50 hover:opacity-100">
                <i className="fa-brands fa-facebook"></i>
              </li>
              <li className="w-16 h-16 flex justify-center items-center text-3xl text-sky-600 cursor-pointer opacity-50 hover:opacity-100">
                <i className="fa-brands fa-google"></i>
              </li>
              <li className="w-16 h-16 flex justify-center items-center text-3xl text-sky-600 cursor-pointer opacity-50 hover:opacity-100">
                <i className="fa-brands fa-github"></i>
              </li>
              <li className="w-16 h-16 flex justify-center items-center text-3xl text-sky-600 cursor-pointer opacity-50 hover:opacity-100">
                <i className="fa-brands fa-x-twitter"></i>
              </li>
            </ul>
          </form>
        </div>
      </div>
    </>
  );
}
