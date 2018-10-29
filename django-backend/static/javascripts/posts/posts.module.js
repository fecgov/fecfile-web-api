(function () {
  'use strict';

  angular
    .module('fecfiler.posts', [
      'fecfiler.posts.controllers',
      'fecfiler.posts.directives',
      'fecfiler.posts.services'
    ]);

  angular
    .module('fecfiler.posts.controllers', []);

  angular
    .module('fecfiler.posts.directives', ['ngDialog']);

  angular
    .module('fecfiler.posts.services', []);
})();