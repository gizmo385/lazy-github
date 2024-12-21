{ pkgs ? import <nixpkgs> {} }:

{
    lh = pkgs.callPackage ./lazy-github.nix { };
}
