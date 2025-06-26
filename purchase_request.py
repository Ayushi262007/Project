from tkinter import *
from tkinter import messagebox
import json
import os
from datetime import datetime
from storage import load_inventory

REQUEST_FILE = "requests.json"
LOW_STOCK_THRESHOLD = 5

def load_requests():
    if os.path.exists(REQUEST_FILE):
        with open(REQUEST_FILE, "r") as file:
            try:
                data = json.load(file)
                cleaned = []
                for req in data:
                    name = req.get("product_name") or req.get("name")
                    qty = req.get("requested_qty") or req.get("quantity")
                    status = req.get("status", "Pending").capitalize()
                    date = req.get("date", datetime.now().strftime("%Y-%m-%d"))

                    if name and qty:
                        cleaned.append({
                            "product_name": name,
                            "requested_qty": int(qty),
                            "status": status,
                            "date": str(date)
                        })
                return cleaned
            except Exception as e:
                print("[Error] Failed to load requests:", e)
                return []
    return []

def save_requests(requests):
    with open(REQUEST_FILE, "w") as file:
        json.dump(requests, file, indent=4)

def auto_generate_requests():
    inventory = load_inventory()
    existing = load_requests()
    existing_names = [req["product_name"] for req in existing if req["status"] == "Pending"]

    new_requests = []
    for item in inventory:
        if item.get("quantity", 0) < LOW_STOCK_THRESHOLD and item.get("name", "") not in existing_names:
            new_requests.append({
                "product_name": item.get("name", ""),
                "requested_qty": LOW_STOCK_THRESHOLD - item.get("quantity", 0),
                "status": "Pending",
                "date": datetime.now().strftime("%Y-%m-%d")
            })

    all_requests = existing + new_requests
    save_requests(all_requests)
    return all_requests

def update_status(index, new_status, refresh_callback):
    requests = load_requests()
    if 0 <= index < len(requests):
        requests[index]["status"] = new_status
        save_requests(requests)
        refresh_callback()

def add_manual_request(name, qty, refresh_callback):
    if not name or not qty:
        messagebox.showwarning("Input Error", "Please fill all fields.")
        return

    try:
        qty = int(qty)
    except ValueError:
        messagebox.showwarning("Invalid Quantity", "Enter a valid number.")
        return

    requests = load_requests()
    requests.append({
        "product_name": name,
        "requested_qty": qty,
        "status": "Pending",
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    save_requests(requests)
    refresh_callback()

def create_purchase_request(parent):
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)

    frame = Frame(parent, bg="#a5dbe9")
    frame.grid(row=0, column=0, sticky="nsew")

    frame.grid_rowconfigure(5, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    Label(frame, text="➕ Manual Purchase Request", font=("Segoe UI", 20, "bold"), bg="#a5dbe9").grid(
        row=0, column=0, columnspan=6, sticky="w", padx=10, pady=(10, 2)
    )

    input_frame = Frame(frame, bg="#a5dbe9")
    input_frame.grid(row=2, column=0, columnspan=6, sticky="w", padx=10, pady=10)

    Label(input_frame, text="Name:", bg="#a5dbe9", font=("Segoe UI", 11, "bold")).pack(side=LEFT, padx=(0, 5))
    entry_name = Entry(input_frame, width=30, font=("Segoe UI", 11))
    entry_name.pack(side=LEFT, padx=(0, 15), ipady=2)

    Label(input_frame, text="Qty:", bg="#a5dbe9", font=("Segoe UI", 11, "bold")).pack(side=LEFT, padx=(0, 5))
    entry_qty = Entry(input_frame, width=10, font=("Segoe UI", 11))
    entry_qty.pack(side=LEFT, padx=(0, 15), ipady=2)

    add_btn = Button(input_frame, text="➕ Add Request", bg="#2980b9", fg="white",
                     font=("Segoe UI", 10, "bold"),
                     command=lambda: add_manual_request(entry_name.get(), entry_qty.get(), refresh_table))
    add_btn.pack(side=LEFT, padx=(0, 10))

    separator = Frame(frame, height=2, bd=1, relief=SUNKEN, bg="gray")
    separator.grid(row=3, column=0, columnspan=6, sticky="ew", padx=10, pady=10)

    Label(frame, text="📋 Purchase Requests", font=("Segoe UI", 12, "bold"), bg="#ecf0f1").grid(
        row=4, column=0, columnspan=6, sticky="w", padx=10, pady=(5, 2)
    )

    table_container = Frame(frame, bg="#ecf0f1")
    table_container.grid(row=5, column=0, columnspan=6, sticky="nsew", padx=10, pady=(0, 10))

    canvas = Canvas(table_container, bg="#ecf0f1", highlightthickness=0)
    scrollbar = Scrollbar(table_container, orient=VERTICAL, command=canvas.yview)
    scrollable_frame = Frame(canvas, bg="#ecf0f1")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)

    def refresh_table():
        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        requests = auto_generate_requests()

        # 🧱 Configure equal weight for all 6 columns
        for col_index in range(6):
            scrollable_frame.grid_columnconfigure(col_index, weight=1)

        # ... All previous code above this remains unchanged ...

        headers = ["#", "Product Name", "Quantity", "Date", "Status", "Actions"]
        for col, header in enumerate(headers):
            Label(scrollable_frame, text=header, font=("Segoe UI", 10, "bold"),
                  bg="#dcdde1", padx=8, pady=6, anchor="center", width=18).grid(row=0, column=col, sticky="nsew", padx=1, pady=1)

        for i, req in enumerate(requests):
            Label(scrollable_frame, text=str(i + 1), bg="white", anchor="center", width=18).grid(row=i+1, column=0, sticky="nsew", padx=1, pady=1)
            Label(scrollable_frame, text=req["product_name"], bg="white", anchor="center", width=18).grid(row=i+1, column=1, sticky="nsew", padx=1, pady=1)
            Label(scrollable_frame, text=req["requested_qty"], bg="white", anchor="center", width=18).grid(row=i+1, column=2, sticky="nsew", padx=1, pady=1)
            Label(scrollable_frame, text=req["date"], bg="white", anchor="center", width=18).grid(row=i+1, column=3, sticky="nsew", padx=1, pady=1)
            Label(scrollable_frame, text=req["status"], bg="white", anchor="center", width=18).grid(row=i+1, column=4, sticky="nsew", padx=1, pady=1)

            action_frame = Frame(scrollable_frame, bg="white")
            action_frame.grid(row=i+1, column=5, sticky="nsew", padx=1, pady=1)

            if req["status"] == "Pending":
                Button(action_frame, text="Approve", bg="#27ae60", fg="white",
                       command=lambda idx=i: update_status(idx, "Approved", refresh_table)).pack(side=LEFT, padx=2)
            elif req["status"] == "Approved":
                Button(action_frame, text="Mark as Ordered", bg="#8e44ad", fg="white",
                       command=lambda idx=i: update_status(idx, "Ordered", refresh_table)).pack(side=LEFT, padx=2)
            else:
                Label(action_frame, text="✔ Done", fg="green", bg="white").pack()

    refresh_table()