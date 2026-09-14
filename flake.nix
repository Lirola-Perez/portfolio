{
  description = "EnergyPlus Python Dev Environment";

  # Defines the package source channel we pull from (NixOS unstable)
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: 
    let
      # Defining the system variable
      system = "x86_64-linux";
      # Import nixpkgs with unfree packages enabled (required for certain tools)
      pkgs = import nixpkgs {
        inherit system;
        # To allow unfree software (like vscode) to run in the shell
        config.allowUnfree = true;
      };

    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          git
          python313
          python313Packages.numpy
          python313Packages.pandas
          python313Packages.tensorflow
          python313Packages.ipykernel
          python313Packages.jupyter
          vscode
          pandoc
          texliveMedium
        ];

        # Runs automatically the moment of typing 'nix develop'
        shellHook = ''
          # Custom styled terminal prompt
          export PS1="\[\e[48;5;17m\]\[\e[1;38;5;82m\] PORTFOLIO Project. \[\e[0m\] \[\e[38;5;82m\]❯\[\e[0m\] \[\e[1;34m\]\w\[\e[0m\] \[\e[38;5;82m\]❯\[\e[0m\] "
          # export PATH="/home/lirola/PROJECT/PORTFOLIO/energyplus:$PATH"
          #echo "--- Initializing Holistic Environment ---"
          echo "--- Clean Nix-LD Environment Initialized ---"
          echo "Tip: Activate your python environment 'source .venv/bin/activate'"
          #echo "Tip: Type 'env-energyplus' to drop inside the FHS binary execution sandbox."
        '';
      };
    };
}
