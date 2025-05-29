"use client";

import { Toaster } from "sonner";
import { notify } from "@/libs/utils";

export default function Notifications() {
  return (
    <div className="space-y-2 p-4">
      <button onClick={() => notify.success("OK")}>Click me</button>
      <button onClick={() => notify.info("OK")}>Click me</button>
      <button onClick={() => notify.warning("OK")}>Click me</button>
      <button onClick={() => notify.error("OK")}>Click me</button>
      <Toaster />
    </div>
  );
}
