module.exports = function(grunt) {

  grunt.initConfig({
    elm: {
      compile: {
        files: {
          "./js/yamana.js": ["./src/Yamana.elm"],
          "./js/plants.js": ["./src/Plants.elm"],
          "./js/plantUpdate.js": ["./src/PlantUpdate.elm"],
          "./js/home.js": ["./src/Home.elm"]
        }
      }
    },
    watch: {
      elm: {
        files: ["./src/Yamana.elm"
               ,"./src/Plants.elm"
               ,"./src/PlantUpdate.elm"
               ,"./src/Home.elm"
               ],
        tasks: ["elm"]
      }
    },
    clean: ["elm-stuff/build-artifacts"]
  });

  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-elm');

  grunt.registerTask('default', ['elm']);

};
