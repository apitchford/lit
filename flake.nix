{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    systems.url = "github:nix-systems/default";
    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.systems.follows = "systems";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3.withPackages (
          ps: with ps; [
            flask
            trafilatura
            ebooklib
            pillow
            requests
            playwright
            python-dotenv
            beautifulsoup4
            lxml
            gunicorn
          ]
        );

        artDomainPackage = pkgs.stdenvNoCC.mkDerivation {
          pname = "art-domain";
          version = "0.1.0";
          src = ./.;

          installPhase = ''
            runHook preInstall

            mkdir -p $out/share/art-domain
            cp app.py $out/share/art-domain/
            cp extractor.py $out/share/art-domain/
            cp image_processor.py $out/share/art-domain/
            cp epub_generator.py $out/share/art-domain/
            cp mailer.py $out/share/art-domain/
            cp requirements.txt $out/share/art-domain/
            cp .env.example $out/share/art-domain/
            cp -r templates $out/share/art-domain/

            runHook postInstall
          '';

          passthru = {
            inherit python;
          };

          meta = {
            description = "Art's web playground, currently serving the Lit Flask app";
            license = pkgs.lib.licenses.mit;
          };
        };
      in
      {
        packages = {
          default = artDomainPackage;
          art-domain = artDomainPackage;
        };

        devShells.default = pkgs.mkShell {
          packages = [
            python
            pkgs.chromium
          ];
        };
      }
    )
    // {
      nixosModules.default =
        {
          config,
          lib,
          pkgs,
          ...
        }:
        let
          inherit (lib)
            mkEnableOption
            mkIf
            mkOption
            types
            optional
            ;

          cfg = config.services.art-domain;
        in
        {
          options.services.art-domain = {
            enable = mkEnableOption "Art's hosted web playground";

            package = mkOption {
              type = types.package;
              default = self.packages.${pkgs.system}.default;
              description = "Package providing the Flask app sources and Python runtime passthru.";
            };

            host = mkOption {
              type = types.str;
              default = "127.0.0.1";
              description = "Bind address for the Gunicorn server.";
            };

            port = mkOption {
              type = types.port;
              default = 5000;
              description = "Port for the Gunicorn server.";
            };

            workers = mkOption {
              type = types.int;
              default = 2;
              description = "Number of Gunicorn workers to run.";
            };

            environmentFile = mkOption {
              type = types.nullOr types.path;
              default = null;
              description = "Optional environment file containing SMTP or app settings.";
            };

            settings = mkOption {
              type = types.attrsOf types.str;
              default = { };
              description = "Extra environment variables for the app service.";
            };

            user = mkOption {
              type = types.str;
              default = "art-domain";
              description = "System user for the service.";
            };

            group = mkOption {
              type = types.str;
              default = "art-domain";
              description = "System group for the service.";
            };
          };

          config = mkIf cfg.enable {
            users.users.${cfg.user} = {
              isSystemUser = true;
              group = cfg.group;
              home = "/var/lib/art-domain";
              createHome = true;
            };

            users.groups.${cfg.group} = { };

            systemd.services.art-domain = {
              description = "Art domain playground app";
              wantedBy = [ "multi-user.target" ];
              after = [ "network-online.target" ];
              wants = [ "network-online.target" ];

              environment =
                {
                  PYTHONUNBUFFERED = "1";
                  DEBUG = "False";
                  HOME = "/var/lib/art-domain";
                  PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH = "${pkgs.chromium}/bin/chromium";
                }
                // cfg.settings;

              serviceConfig = {
                Type = "simple";
                User = cfg.user;
                Group = cfg.group;
                WorkingDirectory = "${cfg.package}/share/art-domain";
                StateDirectory = "art-domain";
                ExecStart = ''
                  ${cfg.package.python}/bin/gunicorn \
                    --chdir ${cfg.package}/share/art-domain \
                    --bind ${cfg.host}:${toString cfg.port} \
                    --workers ${toString cfg.workers} \
                    --timeout 240 \
                    app:app
                '';
                Restart = "on-failure";
                RestartSec = "5s";
                NoNewPrivileges = true;
                PrivateTmp = true;
                ProtectSystem = "strict";
                ProtectHome = true;
                ReadWritePaths = [ "/var/lib/art-domain" ];
              };
            }
            // (
              if cfg.environmentFile == null then
                { }
              else
                { environmentFile = cfg.environmentFile; }
            );
          };
        };
    };
}
