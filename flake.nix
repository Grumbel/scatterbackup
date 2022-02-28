{
  description = "Virtually concatenate files";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-21.11";
    flake-utils.url = "github:numtide/flake-utils";

    bytefmt.url = "github:Grumbel/python-bytefmt";
  };

  outputs = { self, nixpkgs, flake-utils, bytefmt }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in rec {
        packages = flake-utils.lib.flattenTree {
          scatterbackup = pkgs.python3Packages.buildPythonPackage rec {
            pname = "scatterbackup";
            version = "0.1.0";
            src = nixpkgs.lib.cleanSource ./.;
            doCheck = false;
            nativeBuildInputs = [
              pkgs.python3Packages.flake8
              pkgs.python3Packages.pylint
            ];
            buildInputs = [
              pkgs.python3Packages.pyparsing
              pkgs.python3Packages.pyyaml
              pkgs.python3Packages.pyxdg

              bytefmt.defaultPackage.${system}
            ];
           };
        };
        defaultPackage = packages.scatterbackup;
      });
}
