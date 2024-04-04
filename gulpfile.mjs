import gulp from 'gulp';

import sourcemaps from 'gulp-sourcemaps';
import gulpSass from 'gulp-sass';
import * as sass from 'sass';
import gulpAutoprefixer from 'gulp-autoprefixer';
import gulpTypescript from 'gulp-typescript'; // @see https://www.npmjs.com/package/gulp-typescript

/* // UNUSED: Determine the working (project) path
 * import path from 'path';
 * import { fileURLToPath } from 'url';
 * const __filename = fileURLToPath(import.meta.url);
 * const __dirname = path.dirname(__filename);
 * const prjPath = path.resolve(__dirname);
 */

// Working paths...
const srcPath = 'src/';
const staticPath = 'static/';
const sourceAssetsPath = srcPath + 'assets/';
const targetAssetsPath = staticPath + 'assets/';

// Construct sass runner...
const sassRunner = gulpSass(sass);

// Construct ts runner (see `tsconfig.json`...
const tsProject = gulpTypescript.createProject('tsconfig.json');

// Watch...
const watchOptions = {
  // @see: https://gulpjs.com/docs/en/getting-started/watching-files/
  events: 'all',
  /** Omit initial action for watch cycles */
  ignoreInitial: true,
  delay: 500,
  // NOTE: There is a bug with styles compiling watching by
  // `livereload-assets-server`: it takes only previous state, needs to make
  // one extra update
};

// Styles...
const stylesSrcAll = [sourceAssetsPath + '**/*.scss'];
const stylesSrcEntry = sourceAssetsPath + 'styles.scss';
const stylesDest = targetAssetsPath;
function compileStyles() {
  return gulp
    .src(stylesSrcEntry)
    .pipe(sourcemaps.init())
    .pipe(sassRunner().on('error', sassRunner.logError))
    .pipe(gulpAutoprefixer())
    .pipe(sourcemaps.write('.'))
    .pipe(gulp.dest(stylesDest));
  // Delayed final tasks...
  // .on('end', onFinish.bind(null, 'styles')) // TODO?
}
gulp.task('compileStyles', compileStyles);
gulp.task('compileStylesWatch', () => {
  return gulp.watch(stylesSrcAll.concat(stylesSrcEntry), watchOptions, compileStyles);
  // .on('change', onWatchChange); // TODO?
});

// Scripts...
const scriptsSrcAll = [sourceAssetsPath + '**/*.{js,ts}'];
// const scriptsTargetFile = 'scripts.js';
const scriptsDest = targetAssetsPath;
function compileScripts() {
  return gulp
    .src(scriptsSrcAll)
    .pipe(sourcemaps.init())
    .pipe(tsProject())
    .js.pipe(sourcemaps.write('.'))
    .pipe(gulp.dest(scriptsDest));
}
gulp.task('compileScripts', compileScripts);
gulp.task('compileScriptsWatch', () => {
  return gulp.watch(scriptsSrcAll, watchOptions, compileScripts);
  // .on('change', onWatchChange); // TODO?
});

const updateAllTasks = [
  // Watch all tasks...
  'compileStyles',
  'compileScripts',
].filter(Boolean);
gulp.task('updateAll', gulp.parallel.apply(gulp, updateAllTasks));

const watchAllTasks = [
  // Watch all tasks...
  'compileStylesWatch',
  'compileScriptsWatch',
].filter(Boolean);
gulp.task('watchAll', gulp.parallel.apply(gulp, watchAllTasks));
