import React from "react";
import { render, fireEvent, screen } from "@testing-library/react";
import AdminPanel from "./AdminPanel";

global.fetch = jest.fn(() => Promise.resolve({ json: () => ({ success: true }) })) as any;

describe("AdminPanel", () => {
  test("adds document and shows status", async () => {
    render(<AdminPanel />);
    fireEvent.change(screen.getByPlaceholderText("doc id"), { target: { value: "t1" } });
    fireEvent.change(screen.getByPlaceholderText("title"), { target: { value: "T1" } });
    fireEvent.change(screen.getByPlaceholderText("text"), { target: { value: "hello" } });
    fireEvent.click(screen.getByText("Add / Update"));
    const status = await screen.findByText(/success/);
    expect(status).toBeTruthy();
  });
});