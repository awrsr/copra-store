import type { CapacitorConfig } from "@capacitor/cli";

const remoteUrl = process.env.CAPACITOR_SERVER_URL;

const config: CapacitorConfig = {
  appId: "com.copra.staff",
  appName: "Copra Staff",
  webDir: "dist",
  ...(remoteUrl
    ? {
        server: {
          url: remoteUrl,
          cleartext: false,
        },
      }
    : {}),
  plugins: {
    PushNotifications: {
      presentationOptions: ["badge", "sound", "alert"],
    },
  },
};

export default config;
