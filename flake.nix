{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python310Packages;
      in rec {
        packages = flake-utils.lib.flattenTree rec {
          scatterbackup = pythonPackages.buildPythonPackage rec {
            pname = "scatterbackup";
            version = "0.1.0";
            src = nixpkgs.lib.cleanSource ./.;
            doCheck = false;
            nativeBuildInputs = with pythonPackages; [
              flake8
              pylint
            ];
            propagatedBuildInputs = with pythonPackages; [
              pyparsing
              pyyaml
              pyxdg
            ];
          };
          default = scatterbackup;
        };
      }
    );
}
