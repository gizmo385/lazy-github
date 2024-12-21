{
  lib,
  python311Packages,
  fetchFromGitHub,
}:

python311Packages.buildPythonApplication rec {
  pname = "lazy-github";
  version = "0.3.2";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "gizmo385";
    repo = "lazy-github";
    rev = "refs/tags/v${version}";
    hash = "sha256-L5s2q3n18fCvIXjrI6a4LYuvMGVmsdXzx4sDGKk+OTs=";
  };

  build-system = [
    python311Packages.hatchling
    python311Packages.hatch-vcs
  ];
  nativeBuildInputs = [ python311Packages.hatchling python311Packages.hatch-vcs ];
  dependencies = with python311Packages; [
    click
    hishel
    httpx
    pydantic
    textual
  ];

  pythonRelaxDeps = [ "textual" ];

  doCheck = false; # no tests

  meta = with lib; {
    description = "Terminal application to interact with Github";
    license = licenses.mit;
    homepage = "https://github.com/textualize/lazy-github";
    mainProgram = "lh";
  };
}
