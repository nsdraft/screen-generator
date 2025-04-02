document.addEventListener("DOMContentLoaded", function () {
    function showAlert(message) {
        let existingModal = document.querySelector(".custom-modal");
        if (existingModal) {
            existingModal.remove();
        }
        let modal = document.createElement("div");
        modal.classList.add("custom-modal");
        modal.innerHTML = `
            <div class="modal-content">
                <p>${message}</p>
                <button id="closeModal">OK</button>
            </div>
        `;
        document.body.appendChild(modal);
        document.getElementById("closeModal").addEventListener("click", function () {
            modal.remove();
        });
    }

    function validateRequiredFields() {
        let harpName = document.getElementById("harp_name").value.trim();
        let width = document.getElementById("width").value.trim();
        let height = document.getElementById("height").value.trim();
        let backgroundType = document.getElementById("background_type").value;

        if (harpName === "") {
            showAlert("Error: Harp Name is required.");
            return false;
        }
        if (width === "") {
            showAlert("Error: Width is required.");
            return false;
        }
        if (height === "") {
            showAlert("Error: Height is required.");
            return false;
        }
        if (backgroundType === "") {
            showAlert("Error: Harp Type is required.");
            return false;
        }
        return true;
    }

    document.getElementById("poly_ridge").addEventListener("change", function () {
        const overlapSelect = document.getElementById("overlap");
        if (this.value !== "") {
            overlapSelect.disabled = true;
            overlapSelect.value = "";
        } else {
            overlapSelect.disabled = false;
        }
    });

    document.getElementById("center_overlap").addEventListener("change", function () {
        const centerHolesSelect = document.getElementById("center_holes");
        const numHolesInput = document.getElementById("num_center_holes");
        const holeDistancesInput = document.getElementById("hole_distances");

        if (this.value === "Yes") {
            centerHolesSelect.disabled = false;
            numHolesInput.disabled = false;
            holeDistancesInput.disabled = false;
        } else {
            centerHolesSelect.disabled = true;
            numHolesInput.disabled = true;
            holeDistancesInput.disabled = true;
        }
    });

    document.getElementById("poly_ridge").dispatchEvent(new Event("change"));
    document.getElementById("center_overlap").dispatchEvent(new Event("change"));

    function updateDistanceFields() {
        var puQuantity = parseInt(document.getElementById('pu_quantity').value);
        var centerOverlap = document.getElementById('center_overlap').value;
        var container = document.getElementById('distance_fields_container');

        container.innerHTML = '';

        if (isNaN(puQuantity) || puQuantity < 2) {
            return;
        }

        if (centerOverlap === "Yes") {
            var leftCount = Math.floor(puQuantity / 2);
            var rightCount = puQuantity - leftCount;
            var leftFields = leftCount + 1;
            var rightFields = rightCount + 1;

            var html = '<div class="side-container" id="left_container"><h3>Left Side Distances</h3>';
            for (var i = 0; i < leftFields; i++) {
                html += `<label>Left Distance ${i + 1}:</label>`;
                html += `<input type="text" name="left_spacing" required><br><br>`;
            }
            html += '</div>';

            html += '<div class="side-container" id="right_container"><h3>Right Side Distances</h3>';
            for (var j = 0; j < rightFields; j++) {
                html += `<label>Right Distance ${j + 1}:</label>`;
                html += `<input type="text" name="right_spacing" required><br><br>`;
            }
            html += '</div>';

            container.innerHTML = html;
        } else {
            var totalFields = puQuantity + 1;
            var html = '<h3>Spacing Distances</h3>';
            for (var k = 0; k < totalFields; k++) {
                if (k === 0) {
                    html += `<label>Distance from Left Hook to PU Strip 1:</label>`;
                } else if (k === totalFields - 1) {
                    html += `<label>Distance from PU Strip ${puQuantity} to Right Hook:</label>`;
                } else {
                    html += `<label>Distance between PU Strip ${k} and PU Strip ${k + 1}:</label>`;
                }
                html += `<input type="text" name="spacing" required><br><br>`;
            }
            container.innerHTML = html;
        }
    }

    function validateTotalWidth() {
        var totalWidth = parseInt(document.getElementById('width').value);
        var totalSpacing = 0;
        var spacingInputs = document.querySelectorAll('input[name="spacing"], input[name="left_spacing"], input[name="right_spacing"]');

        spacingInputs.forEach(input => {
            totalSpacing += parseInt(input.value) || 0;
        });

        if (totalSpacing !== totalWidth) {
            showAlert(`Error: Total spacing (${totalSpacing} mm) does not match the full width (${totalWidth} mm).`);
            return false;
        }
        return true;
    }

    function validateHoleDistances() {
        var totalHeight = parseInt(document.getElementById('height').value);
        var centerHoles = document.getElementById('center_holes').value;
        var numHoles = parseInt(document.getElementById('num_center_holes').value);

        if (centerHoles === "Yes" && numHoles > 0) {
            var holeDistancesInput = document.getElementById('hole_distances').value;
            var holeDistances = holeDistancesInput.split(',').map(x => parseInt(x.trim()) || 0);
            var totalHoleSpacing = holeDistances.reduce((a, b) => a + b, 0);

            if (totalHoleSpacing !== totalHeight) {
                showAlert(`Error: Total hole distances (${totalHoleSpacing} mm) do not match the full height (${totalHeight} mm).`);
                return false;
            }
        }
        return true;
    }

    function generateCheckboxes() {
        let additionalPUSelect = document.getElementById("additional_pu_strip");
        let checkboxContainer = document.getElementById("checkbox_container");
        let additionalDistancesDiv = document.getElementById("additional_distances");

        if (!additionalPUSelect || !checkboxContainer) return;

        checkboxContainer.innerHTML = "";

        let centerOverlap = document.getElementById("center_overlap").value;

        let leftInputs = document.querySelectorAll('input[name="left_spacing"]');
        let rightInputs = document.querySelectorAll('input[name="right_spacing"]');
        let regularInputs = document.querySelectorAll('input[name="spacing"]');

        let index = 0;

        if (centerOverlap === "Yes") {
            leftInputs.forEach((input, i) => {
                let distance = input.value.trim();
                if (distance !== "") {
                    let checkbox = document.createElement("input");
                    checkbox.type = "checkbox";
                    checkbox.name = "additional_distances";
                    checkbox.value = index;
                    let label = document.createElement("label");
                    label.textContent = `Left ${i + 1} (${distance} mm) `;
                    label.appendChild(checkbox);
                    checkboxContainer.appendChild(label);
                    checkboxContainer.appendChild(document.createElement("br"));
                    index++;
                }
            });

            rightInputs.forEach((input, i) => {
                let distance = input.value.trim();
                if (distance !== "") {
                    let checkbox = document.createElement("input");
                    checkbox.type = "checkbox";
                    checkbox.name = "additional_distances";
                    checkbox.value = index;
                    let label = document.createElement("label");
                    label.textContent = `Right ${i + 1} (${distance} mm) `;
                    label.appendChild(checkbox);
                    checkboxContainer.appendChild(label);
                    checkboxContainer.appendChild(document.createElement("br"));
                    index++;
                }
            });
        } else {
            regularInputs.forEach((input, i) => {
                let distance = input.value.trim();
                if (distance !== "") {
                    let checkbox = document.createElement("input");
                    checkbox.type = "checkbox";
                    checkbox.name = "additional_distances";
                    checkbox.value = index;
                    let label = document.createElement("label");
                    label.textContent = `${distance} mm`;
                    label.appendChild(checkbox);
                    checkboxContainer.appendChild(label);
                    checkboxContainer.appendChild(document.createElement("br"));
                    index++;
                }
            });
        }

        if (index > 0 && additionalPUSelect.value === 'Yes') {
            additionalDistancesDiv.style.display = "block";
        } else {
            additionalDistancesDiv.style.display = "none";
        }
    }

    function updateAdditionalPUPositions() {
        let selectedDistances = Array.from(document.querySelectorAll('input[name="additional_distances"]:checked')).map(cb => parseInt(cb.value));
        let spacingInputs = document.querySelectorAll('input[name="spacing"], input[name="left_spacing"], input[name="right_spacing"]');

        spacingInputs.forEach(input => {
            let distance = parseInt(input.value);
            if (selectedDistances.includes(distance)) {
                input.style.backgroundColor = "orange";
            } else {
                input.style.backgroundColor = "";
            }
        });
    }

    function saveHarpName() {
        let harpName = document.getElementById("harp_name").value;
        localStorage.setItem("harp_name", harpName);
    }

    const textarea = document.getElementById('additional_message');
    textarea.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight + 5) + 'px';
});

    window.addEventListener('load', function () {
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight + 5) + 'px';
    });

    document.querySelector("form").addEventListener("submit", function (event) {
        if (!validateRequiredFields() || !validateTotalWidth() || !validateHoleDistances()) {
            event.preventDefault();
        } else {
            saveHarpName();
        }
    });

    document.getElementById('pu_quantity').addEventListener('input', function() {
        updateDistanceFields();
        generateCheckboxes();
    });
    document.getElementById('center_overlap').addEventListener('change', function() {
        updateDistanceFields();
        generateCheckboxes();
    });
    document.getElementById('additional_pu_strip').addEventListener('change', generateCheckboxes);
    document.getElementById('checkbox_container').addEventListener('change', updateAdditionalPUPositions);

    updateDistanceFields();
});
