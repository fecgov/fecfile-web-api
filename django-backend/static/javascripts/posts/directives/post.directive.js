/**
 * Post
 * @namespace fecfiler.posts.directives
 */
(function () {
    'use strict';

    angular
        .module('fecfiler.posts.directives')
        .directive('post', post);

    /**
     * @namespace Post
     */
    function post() {
        /**
         * @name directive
         * @desc The directive to be returned
         * @memberOf fecfiler.posts.directives.Post
         */
        var directive = {
            restrict: 'E',
            scope: {
                post: '='
            },
            templateUrl: '/static/templates/posts/post.html'
        };

        return directive;
    }
})();