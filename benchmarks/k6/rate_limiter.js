import http from "k6/http";
import { check } from "k6";

export const options = {
    vus: 50,
    duration: "30s",
};

export default function () {
    const response = http.get("http://127.0.0.1:8000/api/test");

    check(response, {
        "status is 200 or 429": (r) =>
            r.status === 200 || r.status === 429,
    });
}