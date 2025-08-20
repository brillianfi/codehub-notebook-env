define([
  'jquery',
  'notebook/js/celltoolbar',
  'base/js/namespace',
  'base/js/events'
],
function ($, celltoolbar, Jupyter, events){
  "use strict";
  // This script will not work if it runs too early since the cells won't be
  // loaded and hence .get_cells() will return an empty array. Therefore we wait
  // for the kernel to be ready.
  Jupyter.notebook.events.on('kernel_ready.Kernel', function() {
    var ctb = celltoolbar.CellToolbar;
    ctb.global_hide();

    function checkGrading(cell){
      // Check if a cell is marked to be graded
      try {
        return cell.metadata.nbgrader.grade;
      }
      catch(err) {
        return false;
      }
    }

    function checkHidden(cell){
      // Check if a cell is marked as hidden
      try {
        return cell.metadata.hideCode;
      }
      catch(err) {
        return false;
      }
    }

    function checkSelfTest(cell){
      // Check if a cell is marked as a self-testing cell
      try {
        return cell.metadata.selfTest;
      }
      catch(err) {
        return false;
      }
    }

    function checkToggle(cell){
      // Check if a cell should toggle displaying a solution
      try {
        return cell.metadata.toggleSolution;
      }
      catch(err) {
        return false;
      }
    }

    function hideCode(cell){
      var c = $(cell.element);
      var cell_index = Jupyter.notebook.find_cell_index(cell);
      // Check if a cell should be hidden
      if (checkHidden(cell)){
        var input = c.find("div.input_area");
        input.hide();
      }
      if (checkSelfTest(cell)){
        // Replace the self testing cell with a button.
        var input = c.find("div.input");
        input.hide();
        // Insert button to execute the input cell and the self tessting cell
        c.append(`<button onclick = "Jupyter.notebook.execute_cells([${cell_index - 1}, ${cell_index}])" style = "background-color: rgb(238,238,238); border: thin solid #CFCFCF;">Click here to check your answer</button>`);
      }
      // Hide all grading cells completely.
      if (checkGrading(cell)){
        c.hide();
      }
      // Execute all toggle cells to show buttons for toggling displaying the solution
      if (checkToggle(cell)){
        var input = c.find("div.input_area");
        input.hide();
        cell.clear_output();
        setTimeout(function(){cell.execute();}, 1000);
      }
    }

    $(".dropdown:contains(Help)").hide();
    // Go through each cell and apply the hideCode function
    $.each(Jupyter.notebook.get_cells(), function(index, cell){ hideCode(cell); });
  });
  console.log('custom.js setup complete');
});
