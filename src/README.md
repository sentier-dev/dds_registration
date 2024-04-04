# Assets

Here are stored source files: template blocks (for include into templates, not templates themselves) and scss style sources (potentially, scripts).

There are two ways to deal with assets supposed to preprocessed, like styles:

## Method 1. To use django filters (like `sass`).

For the first approach take a look at the `COMPRESS_PRECOMPILERS` section in `dds_registration/settings.py`.

For example> the configurations could look like this:

```
('text/x-scss', 'sass --embed-source-map {infile} {outfile}'),
```

It requires sass compiler installed and available in the PATH (It's possible to install it globally from cli with node: `npm i -g sass`).

Set `USE_DJANGO_PREPROCESSORS` in `dds_registration/settings.py` to allow preprocess filters.

## Method 2. To use gulp pipelines (like `compileStyles` or `compileStylesWatch`).

This method requires node and npm and installed dependencies from `package.json`.

Run to install the dependencies:

```
npm install
```

To update all assets:

```
npm run update-assets
```

To watch all assets:

```
npm run watch-assets
```
