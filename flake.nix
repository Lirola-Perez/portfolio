{
  description = "EnergyPlus Python Dev Environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: {
    devShells.x86_64-linux = let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
    in {
      default = (pkgs.buildFHSUserEnvironment {
        name = "energyplus-env";
        targetPkgs = pkgs: with pkgs; [
          python311
          python311Packages.pip
          python311Packages.pandas
          python311Packages.numpy
          python311Packages.tensorflow
          # Any other tools you need
        ];
        runScript = "bash";
      }).env;
    };
  };
}
