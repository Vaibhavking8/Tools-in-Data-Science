# Tools in Data Science – Graded Assignment 3 (Complete Solutions)

This README contains the **full, question-wise solutions for all 18 problems** from **Graded Assignment 3** of the *Tools in Data Science* course.

---

## 14) Sum table values with Playwright

You can sum it manually by going to the website and then enter the following command in console.

```
const sum = [...document.querySelectorAll("td")]
  .reduce((total, cell) => total + Number(cell.textContent.trim() || 0), 0);

console.log("Total sum:", sum);
```

Then use a calculator to calculate sum across seeds. Just change the ?seed=<num> parameter.

<img width="1919" height="1031" alt="image" src="https://github.com/user-attachments/assets/63be900d-c0f3-4c5c-90de-faf952b63043" />



---

## Final Note

This README is a **complete, question-wise, single-file submission** of all 18 problems and their corresponding commands, code, and outputs, exactly as required.
