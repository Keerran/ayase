{
    description = "Open source Karuta bot clone";

    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
        utils.url = "github:numtide/flake-utils";
    };

    outputs = { self, nixpkgs, utils }:
        utils.lib.eachDefaultSystem (system:
            let
                pkgs = import nixpkgs { inherit system; };
            in
            {
                devShell = with pkgs; mkShell {
                    packages = [
                        (python311Full.withPackages (py: [
                            py.certifi
                        ]))
                        postgresql
                    ];
                };
            }
        );
}
