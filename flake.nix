{
  description = "EnergyPlus Python Dev Environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: {
    devShells.x86_64-linux = let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
    in {
      default = (pkgs.buildFHSEnv {
        name = "energyplus-env";
        targetPkgs = pkgs: with pkgs; [
          python312
          python312Packages.pip
          python312Packages.virtualenv
          stdenv.cc.cc.lib
          python312Packages.pandas
          python312Packages.numpy
          python312Packages.tensorflow
          # Any other tools you need
        ];
        runScript = "bash";
      }).env;
       shellHook = ''
          export PS1="\[\e[48;5;17m\]\[\e[1;38;5;82m\] PORTFOLIO Project. \[\e[0m\] \[\e[38;5;82m\]❯\[\e[0m\] \[\e[1;34m\]\w\[\e[0m\] \[\e[38;5;82m\]❯\[\e[0m\] "
          echo "--- Initializing Holistic Environment ---"
        '';
    };
  };
}
