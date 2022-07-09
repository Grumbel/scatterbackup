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
          types-pyyaml = pythonPackages.buildPythonPackage rec {
            pname = "types-PyYAML";
            version = "6.0.9";
            src = pythonPackages.fetchPypi {
              inherit pname version;
              sha256 = "sha256-M651yEuPYf3fDGPpx+VX252xaUrTwu6GKOxe/rtaXps=";
            };
          };

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
              types-setuptools
            ] ++ [
              types-pyyaml
            ];
          };
          default = scatterbackup;
        };
      }
    );
}
