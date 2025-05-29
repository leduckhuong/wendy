import { toast } from "sonner";

export function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export const notify = {
  info:(message:string):void => {
    toast.info(message, {
      style: {
        background: "#3B82F6",
        color: "#FFFFFF",
      },
    });
  },
  success:(message:string):void => {
    toast.success(message, {
      style: {
        background: "#10B981",
        color: "#FFFFFF",
      },
    });
  },
  warning:(message:string):void => {
    toast.warning(message, {
      style: {
        background: "#F97316",
        color: "#FFFFFF",
      },
    });
  },
  error:(message:string):void => {
    toast.error(message, {
      style: {
        background: "#EF4444",
        color: "#FFFFFF",
      },
    });
  }
}

