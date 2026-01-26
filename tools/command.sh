python3 tools/confluence_pdf_playwright.py --parent-url "https://confluence.walmart.com/display/~k0d03gd/UR+low+level+design+and+details" --out-dir exports/pdf --profile-dir ~/.confluence-exporter --interactive-login --dry-run --depth 3 --max-pages 50

python3 tools/confluence_pdf_playwright.py --parent-url "https://confluence.walmart.com/display/~k0d03gd/UR+low+level+design+and+details" --out-dir exports/pdf --profile-dir ~/.confluence-exporter --interactive-login  --depth 3 --max-pages 50


python3 tools/confluence_pdf_playwright.py --parent-url "https://confluence.walmart.com/display/~k0d03gd/UR+low+level+design+and+details" --out-dir exports/pdf --profile-dir ~/.confluence-exporter --interactive-login --dry-run --crawl-mode rest-ancestor --max-pages 100

### Working one below

python3 tools/confluence_pdf_playwright.py --parent-url "https://confluence.walmart.com/display/~k0d03gd/UR+low+level+design+and+details" --out-dir exports/pdf --profile-dir ~/.confluence-exporter  --interactive-login --crawl-mode rest-ancestor --max-pages 100
