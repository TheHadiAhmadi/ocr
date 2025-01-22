<script>
  import { onMount, tick } from "svelte";

  let imageUrl = "/app/image.jpeg";
  let settings = $state({});
  let sliderValue = $state(50);
  let reloader = $state(false);
  let uploadedFile = $state("/app/image.jpeg");
  let convertedFile = $state("/app/converted.jpeg");

  let convertLoading = $state(false);
  let extractLoading = $state(false);

  let ocr_results = $state([]);
  let ocr_results_converted = $state([]);
  let mainImageEl = $state(null);
  let convertedImageEl = $state(null);

  let leftImageTitle = $state("Original Image");
  let rightImageTitle = $state("Converted Image");

  // const baseUrl = "http://localhost:8000/"
const baseUrl = "http://64.176.207.194/";
  async function filesChanged(e) {
    const file = e.target.files[0];

    ocr_results = [];
    ocr_results_converted = [];

    leftImageTitle = "Original Image";
    rightImageTitle = "Converted Image";

    const formData = new FormData();
    formData.append("file", file); // Append the file to FormData

    // Send the file to the backend via POST request
    const response = await fetch(baseUrl + "upload", {
      method: "POST",
      body: formData,
    });

    settings = {
      grayscale: false,
      denoise: false,
      brightness: 100,
      contrast: 100,
      resize_factor: 1,
    };

    if (response.ok) {
      // alert("File uploaded successfully!");
      reloader = !reloader;
    } else {
      alert("Error uploading the file.");
    }
  }

  async function extractTexts() {
    extractLoading = true;

    try {
      const res = await fetch(baseUrl + "ocr", {
        method: "POST",
      }).then((res) => res.json());

      console.log("initialize", res);

      leftImageTitle = "Tesseract";
      rightImageTitle = "Paddle OCR";

      uploadedFile = "/app/image.jpeg";
      convertedFile = "/app/image.jpeg";

      await tick()
      
      ocr_results = res.tesseract_results;
      ocr_results_converted = res.paddle_results;


	setTimeout(() => {
      // Get the actual image and its parent container dimensions
      const parentContainerEl = convertedImageEl.parentElement;

      // Get the original image dimensions (natural width and height)
      const originalWidth = convertedImageEl.naturalWidth;
      const originalHeight = convertedImageEl.naturalHeight;

      // Get the current display size of the image (after scaling)
      const displayWidth = convertedImageEl.clientWidth;
      const displayHeight = convertedImageEl.clientHeight;

      // Calculate scale factors based on the current size and the original size
      const scaleX = displayWidth / originalWidth;
      const scaleY = displayHeight / originalHeight;

      console.log(displayWidth, originalWidth, displayWidth / originalWidth)
      // const scaleX = 2
      // const scaleY = 2


      // const offsetX = (parentContainerEl.clientWidth - displayWidth) / 2;
      // const offsetY = (parentContainerEl.clientHeight - displayHeight) / 2;

      // const scaleX = displayWidth / convertedImageEl.naturalWidth;
      // const scaleY = displayHeight / convertedImageEl.naturalHeight;

      // Update bounding box values based on the scale factors
      const updatedOcrResults = ocr_results.map((result) => {
        return {
          ...result,
          bounding_box: {
            left: result.bounding_box.left * scaleX / settings.resize_factor,
            top: result.bounding_box.top * scaleY / settings.resize_factor,
            width: result.bounding_box.width * scaleX / settings.resize_factor,
            height: result.bounding_box.height * scaleY / settings.resize_factor,
          },
        };
      });

      const updatedOcrResultsConverted = ocr_results_converted.map((result) => {
        return {
          ...result,
          bounding_box: {
            left: result.bounding_box.left * scaleX / settings.resize_factor,
            top: result.bounding_box.top * scaleY / settings.resize_factor,
            width: result.bounding_box.width * scaleX / settings.resize_factor,
            height: result.bounding_box.height * scaleY / settings.resize_factor,
          },
        };
      });

      // Update state or call a function to render the updated results
      ocr_results = updatedOcrResults;
      ocr_results_converted = updatedOcrResultsConverted;
}, 1000)
    } catch (err) {
      //
    } finally {
      extractLoading = false;
    }
  }

  onMount(async () => {
    const res = await fetch(baseUrl + "load").then((res) =>
      res.json()
    );
    console.log("initialize", res);
    settings = res.settings;
  });

  async function rotateClock() {
    const res = await fetch(baseUrl + "rotate-clock", {
      method: "POST",
    }).then((res) => res.json());
    reloader = !reloader;
  }

  async function rotateAntiClock() {
    const res = await fetch(baseUrl + "rotate-anticlock", {
      method: "POST",
    }).then((res) => res.json());
    reloader = !reloader;
  }

  async function convert() {
    try {
      ocr_results = [];
    ocr_results_converted = [];

      convertLoading = true
    const response = await fetch(baseUrl + "convert", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(settings),
    });

    leftImageTitle = "Original Image";
    rightImageTitle = "Converted Image";

    if (response.ok) {
      // Refresh the image to reflect changes
      reloader = !reloader;
    } else {
      alert("Error converting the image");
    }
  }catch(err) {
    // 
  } finally {
    convertLoading = false
  }

    // call api and reload the image.
  }

  $effect(() => {
    console.log(reloader);
    uploadedFile = `/app/image.jpeg?t=${new Date()}`;
    convertedFile = `/app/converted.jpeg?t=${new Date()}`;
  });
</script>

<main class="flex bg-[#404244]">
  <!-- Left Form Section -->
  <div class="w-1/4 p-6 bg-[#232425] text-white border-r border-[#505254] space-y-6">
    <input type="file" name="file" id="" onchange={filesChanged} />

    <div class="flex gap-4 items-center">
      <button
        onclick={rotateAntiClock}
        class="flex items-center justify-center w-full px-4 py-2 border border-blue-500 text-blue-500 font-semibold rounded-lg hover:text-white hover:bg-blue-600"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="32"
          height="32"
          viewBox="0 0 24 24"
          ><path
            fill="currentColor"
            d="M13 22q-1.275 0-2.5-.35T8.2 20.6l1.45-1.45q.775.425 1.625.638T13 20q2.925 0 4.962-2.038T20 13t-2.037-4.962T13 6h-.15l1.55 1.55L13 9L9 5l4-4l1.4 1.45L12.85 4H13q3.75 0 6.375 2.625T22 13q0 1.875-.712 3.513t-1.925 2.85t-2.85 1.925T13 22m-6-3l-6-6l6-6l6 6zm0-2.85L10.15 13L7 9.85L3.85 13zM7 13"
          /></svg
        >
      </button>
      <button
        onclick={rotateClock}
        class="flex items-center justify-center w-full px-4 py-2 border border-blue-500 text-blue-500 font-semibold rounded-lg hover:text-white hover:bg-blue-600"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="32"
          height="32"
          viewBox="0 0 24 24"
          ><path
            fill="currentColor"
            d="M11 22q-1.875 0-3.512-.712t-2.85-1.925t-1.926-2.85T2 13q0-3.75 2.625-6.375T11 4h.15L9.6 2.45L11 1l4 4l-4 4l-1.4-1.45L11.15 6H11Q8.075 6 6.038 8.038T4 13t2.038 4.963T11 20q.875 0 1.725-.213t1.625-.637l1.45 1.45q-1.075.7-2.3 1.05T11 22m6-3l-6-6l6-6l6 6zm0-2.85L20.15 13L17 9.85L13.85 13zM17 13"
          /></svg
        >
      </button>
    </div>

    <form onsubmit={convert} class="space-y-4">
      <!-- Brightness Input -->
      <div class="flex gap-4">
        <div class="flex gap-2">
          <input
            type="checkbox"
            id="grayscale"
            bind:checked={settings.grayscale}
          />
          <label for="grayscale" class="block text-sm font-medium"
            >Grayscale</label
          >
        </div>

        <div class="flex gap-2">
          <input type="checkbox" id="denoise" bind:checked={settings.denoise} />
          <label for="denoise" class="block text-sm font-medium">
            Denoise
          </label>
        </div>
      </div>

      <!-- Contrast Input -->
      <div>
        <label for="contrast" class="block text-sm font-medium">Contrast</label>
        <input
          type="range"
          id="contrast"
          min="0"
          max="200"
          bind:value={settings.contrast}
          class="w-full"
        />
        <div class="text-sm">Contrast: {settings.contrast}%</div>
      </div>

      <!-- brightness Input -->
      <div>
        <label for="brightness" class="block text-sm font-medium"
          >brightness</label
        >
        <input
          type="range"
          id="brightness"
          min="0"
          max="200"
          bind:value={settings.brightness}
          class="w-full"
        />
        <div class="text-sm">brightness: {settings.brightness}%</div>
      </div>

      <!-- resize_factor Input -->
      <div>
        <label for="resize_factor" class="block text-sm font-medium"
          >resize factor</label
        >
        <input
          type="range"
          id="resize_factor"
          min="0.25"
          step="0.25"
          max="8"
          bind:value={settings.resize_factor}
          class="w-full"
        />
        <div class="text-sm">resize factor: {settings.resize_factor}</div>
      </div>

      <div>
        <button
          type="submit"
          data-loading={convertLoading}
          class="w-full px-4 py-2 data-[loading=true]:opacity-50 bg-blue-500 text-white font-semibold rounded-lg hover:bg-blue-600"
        >
          Convert
        </button>
      </div>
    </form>

    <div class="flex flex-col gap-2">
      <button
        onclick={extractTexts}
        type="button"
        data-loading={extractLoading}
        class="w-full px-4 py-2 data-[loading=true]:opacity-50 bg-green-500 text-white font-semibold rounded-lg hover:bg-green-600"
      >
        Extract Texts
      </button>
    </div>
  </div>

  {#key reloader}
    <!-- Right Image Section -->
    <div class="flex items-center justify-center w-3/4 p-6">
      <!-- Image with dynamic styles based on form inputs -->
      <!-- Image comparison slider -->
      <div class="border border-[#505254] preview relative w-full h-full bg-[#404244] overflow-auto">
        <!-- Container for the images -->
        <div
          class="absolute w-full"
          style="clip-path: inset(0 calc({100 - sliderValue}% + 0.5px) 0 0);"
        >
          <!-- Original Image -->
          <div class="max-content h-full">
            <img
              bind:this={mainImageEl}
              src={uploadedFile}
              alt="Original Image"
              class="w-full h-full object-contain object-left-top"
            />

            <svg
              class="absolute top-0 left-0 w-full h-full pointer-events-none"
            >
              {#each ocr_results as result}
                {@const color =
                  result.confidence > 90
                    ? "green"
                    : result.confidence > 75
                      ? "yellow"
                      : result.confidence > 50
                        ? "red"
                        : "black"}
                <rect
                  x={result.bounding_box.left}
                  y={result.bounding_box.top}
                  width={result.bounding_box.width}
                  height={result.bounding_box.height}
                  stroke={color}
                  onclick={(e) => e.target.classList.add("hidden")}
                  fill="none"
                  stroke-width="1"
                  class="cursor-pointer fill-black/5 hover:fill-gray-200/20"
                >
                  <title>{result.text} ({result.confidence}%)</title>
                </rect>
              {/each}
              <!-- Rectangles will be inserted here -->
            </svg>
          </div>
        </div>

        <!-- Converted Image (this one will be cropped based on the slider) -->
        <div
          class="absolute w-full"
          style="clip-path: inset(0 0 0 calc({sliderValue}% + 0.5px));"
        >
          <img
            bind:this={convertedImageEl}
            src={convertedFile}
            alt="Converted Image"
            class="w-full h-full object-contain object-left-top"
          />

          <svg class="absolute top-0 left-0 w-full h-full pointer-events-none">
            {#each ocr_results_converted as result}
              {@const color =
                result.confidence > 90
                  ? "green"
                  : result.confidence > 75
                    ? "yellow"
                    : result.confidence > 50
                      ? "red"
                      : "black"}
              <rect
                title={result.text}
                x={result.bounding_box.left}
                y={result.bounding_box.top}
                width={result.bounding_box.width}
                height={result.bounding_box.height}
                stroke={color}
                onclick={(e) => e.target.classList.add("hidden")}
                fill="none"
                stroke-width="1"
                class="cursor-pointer fill-black/5 hover:fill-gray-200/20"
              >
                <title>{result.text} ({result.confidence}%)</title>
              </rect>
            {/each}
            <!-- Rectangles will be inserted here -->
          </svg>
        </div>
        <div class="sticky flex justify-between text-sm px-2 font-bold text-white left-0 top-0">
      
          <input
          type="range"
          min="0"
          max="100"
          bind:value={sliderValue}
          class="absolute left-0 right-0 w-full"
        />
        <div class="pointer-events-none z-40">
          {leftImageTitle}
        </div>
        <div class="pointer-events-none z-40">
          {rightImageTitle}
        </div>

        </div>

      
      </div>

      <!-- Slider to control the mask -->
    </div>
  {/key}
</main>

<style>
  main {
    height: 100vh;
    color-scheme: dark;
    font-family: Arial, sans-serif;
  }

  .relative {
    position: relative;
  }

  .absolute {
    position: absolute;
  }

  .preview {
    /* zoom: 1.5; */
    user-select: none;
  }

  .preview svg {
    user-select: all;
    pointer-events: all;
  }

  .preview input[type="range"] {
    -webkit-appearance: none;
    appearance: none;
    /* height: 5px; */
    background: rgba(0, 0, 0, 0.5);
    outline: none;
    transition: background 0.3s;
    z-index: 10;
  }

  .preview input[type="range"]:hover {
    background: rgba(0, 0, 0, 0.4);
  }

  .preview input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    background: #4caf50;
    cursor: pointer;
    border-radius: 50%;
  }

  .preview input[type="range"]::-moz-range-thumb {
    width: 20px;
    height: 20px;
    background: #4caf50;
    cursor: pointer;
    border-radius: 50%;
  }
</style>
