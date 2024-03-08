import gulp from 'gulp';

import sourcemaps from 'gulp-sourcemaps';
import gulpSass from 'gulp-sass';
import * as sass from 'sass';
import gulpAutoprefixer from 'gulp-autoprefixer';

/* // UNUSED: Determine the working (project) path
 * import path from 'path';
 * import { fileURLToPath } from 'url';
 * const __filename = fileURLToPath(import.meta.url);
 * const __dirname = path.dirname(__filename);
 * const prjPath = path.resolve(__dirname);
 */

// Construct sass runner
const sassRunner = gulpSass(sass);

const staticPath = 'static/';
const blocksPath = staticPath + 'blocks/';

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
const stylesSrcAll = [blocksPath + '**/*.scss'];
const stylesSrcEntry = blocksPath + 'styles.scss';
const stylesDest = blocksPath;
function compileStyles() {
  return (
    gulp
      .src(stylesSrcEntry)
      .pipe(sourcemaps.init())
      .pipe(sassRunner().on('error', sassRunner.logError))
      .pipe(gulpAutoprefixer())
      // .pipe(gulpConcat('styles.css'))
      .pipe(sourcemaps.write('.'))
      .pipe(gulp.dest(stylesDest))
      // Delayed final tasks...
      // .on('end', onFinish.bind(null, 'styles'))
  );
}
gulp.task('compileStyles', compileStyles);
gulp.task('compileStylesWatch', () => {
  return gulp
    .watch(stylesSrcAll.concat(stylesSrcEntry), watchOptions, compileStyles)
    // .on('change', onWatchChange);
});

const updateAllTasks = [
  // Watch all tasks...
  'compileStyles',
].filter(Boolean);
gulp.task('updateAll', gulp.parallel.apply(gulp, updateAllTasks));
// gulp.task('recreateAll', gulp.series(['cleanGenerated', 'updateAll']));

const watchAllTasks = [
  // Watch all tasks...
  'compileStylesWatch',
].filter(Boolean);
gulp.task('watchAll', gulp.parallel.apply(gulp, watchAllTasks));
