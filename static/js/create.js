$(document).ready(function () {
  let currentChoices = 2;
  let hasPollQuestion = false;
  let currentCustomDemos = 0;

  function updateSubmitButtonState() {
    let filledChoices = 0;
    $("#choicesWrapper input").each(function () {
      if ($(this).val().trim() !== "") {
        filledChoices++;
      }
    });
    if (filledChoices >= 2 && hasPollQuestion) {
      $("#submitPoll").removeAttr("disabled");
    } else {
      $("#submitPoll").attr("disabled", true);
    }
  }

  $("#addChoice").on("click", function () {
    if (currentChoices < maxChoices) {
      $("#choicesWrapper").append(
        `<input type="text" name="choice${
          currentChoices + 1
        }" class="form-control mb-2 poll-option" placeholder="Option ${
          currentChoices + 1
        }" />`
      );
      currentChoices++;
      console.log("lmao");
      updateSubmitButtonState();
    }
  });

  $("#removeChoice").on("click", function () {
    if (currentChoices > 2) {
      $("#choicesWrapper .poll-option:last-child").remove();
      currentChoices--;
      updateSubmitButtonState();
    }
  });

  $("#addCustomDemo").on("click", function () {
    if (currentCustomDemos < maxCustomDemoOptions) {
      $("#customDemoWrapper").append(
        `<input type="text" name="customDemo${
          currentCustomDemos + 1
        }" class="form-control mb-2" placeholder="Custom Demographic ${
          currentCustomDemos + 1
        }" />`
      );
      currentCustomDemos++;
    }
  });

  $("#removeCustomDemo").on("click", function () {
    if (currentCustomDemos > 0) {
      $("#customDemoWrapper input:last-child").remove();
      currentCustomDemos--;
    }
  });

  // Check whenever an input in choicesWrapper changes
  $("#choicesWrapper").on("input", "input", function () {
    updateSubmitButtonState();
  });

  // Update hasPollQuestion whenever an input in pollQuestion changes
  $("#pollQuestion").on("input", function () {
    if ($(this).val().length > 5) {
      hasPollQuestion = true;
    } else {
      hasPollQuestion = false;
    }
    updateSubmitButtonState();
  });
});
