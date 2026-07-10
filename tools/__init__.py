"""
tools — Paraguay Geodata

Every script in this directory is a single-source-of-truth executable for one
piece of the pipeline. Run each via:

    cd /root/paraguay-geodata && python3 -m tools.<script_name> [...args]

Conventions:
- Tools accept --dry-run where they produce side effects
- Tools write to data/ (gitignored) or exports/web/data/ (Pages-deployable small files)
- Heavy raster outputs go to exports/big_data_excluded_from_deploy/ (R2-backed)
- Every tool's docstring points at the class-level skill it inherits from
"""
