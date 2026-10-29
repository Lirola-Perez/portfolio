{
  description = "EnergyPlus Python Dev Environment";

  # Defines the package source channel we pull from (NixOS unstable)
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  nixConfig = {
    max-jobs = 3;
    cores = 4;
  };

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

      myPython = pkgs.python313.withPackages (ps: with ps; [
        pydantic
        black
        pandas
        numpy
        matplotlib
        scikit-learn
        uv
        # mlxtend contains the keras modules
        (mlxtend.overridePythonAttrs (old: {
          doCheck = false; # Check deactivated for avoiding numerical errors
        }))
        seaborn
        tensorflow
        ipython
        ipywidgets
        jupyterlab
        pytest
        nltk
        fastapi
        uvicorn
        psycopg2-binary
        flask
        sqlalchemy

        (ps.buildPythonPackage rec {
          pname = "eppy";
          version = "0.5.68";
          src = ps.fetchPypi {
            inherit pname version;
            hash = "sha256-ZxGtYiNmx0UomGY9v37O6pso4SeWXzG+VH31ec/nsrY="; # Nix will output the correct hash if left blank
            };
          pyproject = true;
          # Use hatchling instead of setuptools
          build-system = [ ps.hatchling ];
          propagatedBuildInputs = [ 
              ps.numpy 
              ps.scipy 
              ps.beautifulsoup4
              ps.lxml
              ps.munch
              ps.decorator
            ];

            dontCheckRuntimeDeps = true;
            doCheck = false;
          })
      ]);

    in {
      
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          git
          direnv
          myPython
          vscode
          pandoc
          texliveMedium
          chromium
        ];

        # Runs automatically the moment of typing 'nix develop'
        shellHook = ''
          # Custom styled terminal prompt
          export PS1="\[\e[48;5;17m\]\[\e[1;38;5;82m\] PORTFOLIO Project. \[\e[0m\] \[\e[38;5;82m\]❯\[\e[0m\] \[\e[1;34m\]\w\[\e[0m\] \[\e[38;5;82m\]❯\[\e[0m\] "
          # export PATH="/home/lirola/PROJECT/PORTFOLIO/energyplus:$PATH"
          #echo "--- Initializing Holistic Environment ---"
          echo "--- Clean Nix-LD Environment Initialized ---"
          echo "--- WARNING: Removing .venv folder before entering environment for package update ---"
          echo "--- rm -rf .venv"
          if [ ! -d ".venv" ] || [ ! -f ".venv/bin/python" ]; then
            echo "--- Setting up clean virtual environment with Python 3.13 ---"
            #########################################################################################
            # ATTENTION!: if you install sth with pip -> use first rm -rf .venv to "reload" this part.
            #########################################################################################
            rm -rf .venv
            ${myPython}/bin/python -m venv --system-site-packages .venv
            .venv/bin/pip install --upgrade pip
            # Install Jupyter server tools specifically inside the venv to satisfy VS Code's requirements
            #.venv/bin/pip install jupyter jupyterlab ipykernel keras dvc 
            #.venv/bin/pip install tensorflow-datasets tfds-nightly 
            # Register the kernel globally for user-space discovery in IDEs like VS Code
            #.venv/bin/python -m ipykernel install --user --name=ml-course --display-name "Python (ML Course)"
          fi
          echo "Tip: Activate your python environment 'source .venv/bin/activate'"
          echo "source .venv/bin/activate"
        '';
      };
    };
}
