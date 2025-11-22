{pkgs}: {
  channel = "stable-24.11";
  packages = [
    pkgs.nodejs_20
    pkgs.zulu
    pkgs.python311
    pkgs.gcc-unwrapped.lib
    pkgs.firebase-tools  # <-- This is the new line
  ];
  env = {};
  idx = {
    extensions = [];
    workspace = {
      onCreate = {
        default.openFiles = [
          "src/app/page.tsx"
        ];
      };
    };
    previews = {
      enable = true;
      previews = {
        web = {
          command = ["npm" "run" "dev" "--" "--port" "$PORT" "--hostname" "0.0.0.0"];
          manager = "web";
        };
      };
    };
  };
}