let currentId = 0;
let optionId = 0;

const dropfield = document.querySelector("#dropField");
const designer = document.getElementById("designer");

const optionTypes = ["checkboxes", "dropdown"]

function dragstartHandler (event) {
    // Determine the template that will be used when the tool is dropped on the designer.
    const srcId = event.target.id;

    if (srcId.includes("question")) {
        // Set transfer data to the id of the question that will be reordered.
        event.dataTransfer.setData("text/reorder", srcId);
    }
    else {
        let templateId = srcId + "-template";

        // Set transfer data to the id of the template that will be cloned.
        event.dataTransfer.setData("text/plain", templateId);
    }
}

function designerDropHandler (event) {
    if (event.dataTransfer.getData("text/reorder")) {
        reorderFields(event);
    }
    else {
        addField(event);
    }
}

function dblclickHandler (event) {
    const srcId = event.target.closest("div.form-tool").id;

    let templateId = srcId + "-template";

    addField(event, templateId);
}

function reorderFields(event) {
    // Get the id of the field being reordered.
    const srcId = event.dataTransfer.getData("text/reorder");
    const draggedElem = document.getElementById(srcId);

    // Get the element that the dragged element is being dropped relative to.
    let elem = document.elementFromPoint(event.clientX, event.clientY);

    const relativeElem = elem.closest('[id^="question_"]');

    // Determine if the dragged element should be placed before or after the relative element.
    const afterOrBefore = positionRelativeElem(event.clientY, event.clientX);

    // Place the dragged element after or before the relative element.
    if (afterOrBefore === "after") {
        relativeElem.after(draggedElem);
    }
    else {
        relativeElem.before(draggedElem);
    }
}

function positionRelativeElem(y, x) {
    // Get the bounding box of the element at the coordinates provided
    const elem = document.elementFromPoint(x, y);

    // Get the bounding box of the question element that contains the target element.
    const box = elem.closest('[id^="question_"]').getBoundingClientRect();

    // Determine if the y coordinate of the mouse is above or below the middle of the element.
    const middleY = box.top + (box.height / 2);

    // Return "before" if dropped on the top half of the target question, and after if on the bottom half.
    if (middleY > y) {
        return "before";
    }
    return "after";
}

function addField(event, templateId = null) {
    // Increment the question counter.
    currentId++;

    event.preventDefault();
    // Get the name of the template to clone
    const data = event instanceof DragEvent ? event.dataTransfer.getData("text/plain") : templateId;

    // Select the designer card, and the template
    const parent = document.getElementById("designer");
    const template = document.getElementById(data);

    // Clone the template, set the id of the template to be used later if we need to remove the question
    // and add the template to the designer.
    const clone = document.importNode(template.content, true)
    const cardDiv = clone.querySelector(".card");
    cardDiv.id = `question_${currentId}`
    cardDiv.addEventListener("dragstart", dragstartHandler);
    if (designer.children.length === 1) {
        dropfield.classList.remove("visible")
        dropfield.classList.add("invisible", "hidden");
    }
    parent.append(clone);
}

function removeField (elem) {
    // Remove a question from the designer.
    elem.remove();

    if (designer.children.length === 1) {
        dropfield.classList.remove("invisible", "hidden");
        dropfield.classList.add("visible");
    }
}

function addOption (elem) {
    optionId++;

    const template = document.getElementById("list-group-item-template")
    const listGroupItemClone = document.importNode(template.content, true)

    const listGroup = elem.querySelector("ul")
    listGroupItemClone.querySelector("li").id = `option_${optionId}`
    listGroup.append(listGroupItemClone)
}

function getQuestions() {
    const questions = [];
    designer.querySelectorAll("[id^='question_']").forEach(elem => {
        questions.push(elem);
    })
    return questions;
}

function customReportValidity(elem) {
    const elemValid = elem.checkValidity();

    if (!elemValid) {
        elem.classList.add("invalid-field");
        if (elem.parentElement.classList.contains("d-flex")) {
            elem = elem.parentElement;
        }
        elem.parentElement.querySelector(".invalid-feedback").style.display = "block";

        return false;
    }

    if (elem.classList.contains("invalid-field")) {
        elem.classList.remove("invalid-field");
        if (elem.parentElement.classList.contains("d-flex")) {
            elem = elem.parentElement;
        }
        elem.parentElement.querySelector(".invalid-feedback").style.display = "none";
    }

    return true;
}

function validateForm() {
    let validForm;

    const nameValid = customReportValidity(document.getElementById("name"))
    const descriptionValid = customReportValidity(document.getElementById("description"));
    const activeValid = customReportValidity(document.getElementById("active"))

    validForm = nameValid && descriptionValid && activeValid;

    const questions = getQuestions();

    if (questions.length === 0) {
        console.log("A form must have questions");
        validForm = false;
    }

    for (let i = 0; i < questions.length; i++) {
        const question = questions[i];
        const questionType = question.closest("[id^='question_']").getAttribute("data-field");

        const questionField = question.querySelector("[id='question']");
        const options = question.querySelectorAll("[id='option']");
        if (!(options.length < 2)) {
            for (let i = 0; i < options.length; i++) {
                const option = options[i];
                const optionValid = customReportValidity(option);
                validForm = validForm && optionValid;
            }
        }

        if (optionTypes.includes(questionType) && options.length < 2) {
            question.closest("[id^='question_']")
                .querySelector("#options_card")
                .querySelector(".card-footer").style.color = "red";

            validForm = false;
        }
        else if (optionTypes.includes(questionType) && options.length >= 2){
            question.closest("[id^='question_']")
                .querySelector("#options_card")
                .querySelector(".card-footer").style.color = "";
        }

        const questionValid = customReportValidity(questionField);
        validForm = validForm && questionValid;
    }

    console.log(`This form is ${validForm ? "valid" : "invalid"}`)
    return validForm;
}

function buildFormJson() {
    let validForm = validateForm();

    if (!validForm) {
        return {error: "Form invalid."};
    }

    const formJson = {
        name: document.getElementById("name").value,
        description: document.getElementById("description").value,
        active: document.getElementById("active").checked,
        questions: []
    }

    const questions = getQuestions();

    for (let i = 0; i < questions.length; i++) {
        const question = questions[i];
        const questionField = question.querySelector("[id='question']");
        const required = question.querySelector("[id='required']").checked;
        const fieldType = question.closest("[id^='question_']").getAttribute("data-field");

        const questionJson = {
            type: fieldType,
            question: questionField.value,
            required: required,
        }

        if (optionTypes.includes(fieldType)) {
            const options = question.querySelectorAll("[id^='option_']");
            const optionsList = [];
            for (let i = 0; i < options.length; i++) {
                const option = options[i];
                optionsList.push(option.querySelector("[id='option']").value);
            }

            questionJson.options = optionsList;
        }

        formJson.questions.push(questionJson);
    }

    return formJson;
}

function submitForm(csrf_token) {
    const formJson = buildFormJson();

    if ("error" in formJson) {
        console.log(`Unable to submit form: ${formJson.error}`)
        return;
    }

    console.log(JSON.stringify(formJson))
    fetch(window.location.href, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
        },
        body: JSON.stringify(formJson)
    })
    .then(response => {
        console.log(`Response Status: ${response.status}`)
        if (response.ok){
            successNotification();
        }
    })
    .catch((error) => {
        console.log(error)
    })
}

function successNotification() {
    const successMessageP = document.getElementById("success-message");
    const countdownP = document.getElementById("countdown");

    if (window.location.href.includes("edit")) {
        successMessageP.innerHTML = "Form updated successfully!";
    }
    else {
        successMessageP.innerHTML = "Form created successfully!";
    }

    const successModal = document.getElementById("success-modal");
    const modal = new bootstrap.Modal(successModal);
    modal.show()

    let timeLeft = 11;

    const timer = setInterval(() => {
        countdownP.innerHTML = timeLeft - 1;
        timeLeft--;
        if (timeLeft === 0) {
            clearInterval(timer);

            window.location.href = "/hrapps/";
        }
    }, 1000);
}