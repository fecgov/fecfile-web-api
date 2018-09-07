/**
 * Posts
 * @namespace fecfiler.posts.directives
 */
(function () {
    'use strict';

    angular
        .module('fecfiler.posts.directives')
        .directive('posts', posts);

    /**
     * @namespace Posts
     */
    function posts() {
        /**
         * @name directive
         * @desc The directive to be returned
         * @memberOf fecfiler.posts.directives.Posts
         */
        var directive = {
            controller: 'PostsController',
            controllerAs: 'vm',
            restrict: 'E',
            scope: {
                posts: '='
            },
            templateUrl: '/static/templates/posts/posts.html'
        };

        return directive;
    }
})();