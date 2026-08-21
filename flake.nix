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

      # =========================================================================
      # INNER LAYER: The FHS Sandbox ("The Ubuntu-like fake filesystem")
      # =========================================================================
      # This creates a lightweight chroot-like sandbox environment. 
      # It maps standard directories like /lib64 and /usr/bin temporarily so 
      # pre-compiled binaries (like EnergyPlus) find the dependencies they expect.
      energyPlusEnv = pkgs.buildFHSEnv {
        name = "energyplus-env";
        # Tools and libraries available ONLY inside this sandbox layer
        targetPkgs = pkgs: with pkgs; [
          stdenv.cc.cc.lib # C++ standard libraries required for ML/TensorFlow wheels
          # --- EnergyPlus GRAPHICS LIBRARIES ---
          libX11
          libXext
          (python313.withPackages (ps: with ps; [
            pip
            virtualenv
            pandas
            numpy
            tensorflow
          ]))
        ]; 
        runScript = "bash";
        #extraBuildCommands = "export PATH=${PWD}/energyplus:${PATH}"; # Starts a bash shell when the sandbox is entered
        profile = ''
            echo "--- Initializing FHS Sandbox for Binaries ---"
            
            # Force the loader to find X11 and other standard libraries
            export LD_LIBRARY_PATH="${pkgs.libX11.out}/lib:${pkgs.libXext.out}/lib:${pkgs.zlib.out}/lib:${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            export PATH="$/home/lirola/PROJECT/PORTFOLIO/energyplus:$PATH"
            echo "Tip: Run 'source .venv/bin/activate' to use your pip/eppy environment."
            '';
      };

    in {
      # =========================================================================
      # OUTER LAYER: The Standard Nix Development Shell (mkShell)
      # =========================================================================
      # Typing 'nix develop', it lands here first. This layer handles 
      # this custom terminal styling and triggers the shell startup scripts.
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          ### EnergyPlus Sandbox's call #############
          # We inject our inner FHS sandbox wrapper into this shell's build inputs
          energyPlusEnv
          ###########################################
          pkgs.git
          ####### Python Interpreter ################
          # Including again the Python for the VSCode interpreter to point same version and pkgs
          pkgs.python313
          pkgs.python313Packages.numpy
          pkgs.python313Packages.pandas
          pkgs.python313Packages.tensorflow
          ##########################################
          pkgs.vscode
        ];

        # Runs automatically the moment of typing 'nix develop'
        shellHook = ''
          # Custom styled terminal prompt
          export PS1="\[\e[48;5;17m\]\[\e[1;38;5;82m\] PORTFOLIO Project. \[\e[0m\] \[\e[38;5;82m\]❯\[\e[0m\] \[\e[1;34m\]\w\[\e[0m\] \[\e[38;5;82m\]❯\[\e[0m\] "
          export PATH="/home/lirola/PROJECT/PORTFOLIO/energyplus:$PATH"
          echo "--- Initializing Holistic Environment ---"
          echo "Tip: Type 'energyplus-env' to drop inside the FHS binary execution sandbox."
        '';
      };
    };
}
