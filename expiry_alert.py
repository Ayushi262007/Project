from tkinter import *   
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from storage import load_inventory, save_inventory

def create_expiry_alert(parent):
    alert_frame = Frame(parent, bg="#a5dbe9", padx=20, pady=20)
    alert_frame.grid(row=0, column=0, sticky="nsew")

    Label(alert_frame, text="⚠ Expiry Alerts", font=("Segoe UI", 22, "bold"),
          bg="#a5dbe9", fg="#c0392b").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

    # Combined filter and buttons in one row
    control_frame = Frame(alert_frame, bg="#a5dbe9")
    control_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

    Label(control_frame, text="Filter:", font=("Segoe UI", 14), bg="#a5dbe9").grid(row=0, column=0, sticky="w")
    filter_option = StringVar()
    filter_option.set("7 Days")
    OptionMenu(control_frame, filter_option, "7 Days", "30 Days", "Expired").grid(row=0, column=1, padx=5)

    Button(control_frame, text="🔁 Refresh", command=lambda: refresh_table(),
           bg="#2980b9", fg="white", padx=10, pady=5).grid(row=0, column=2, padx=(20, 10))
    Button(control_frame, text="🗑 Remove", command=lambda: archive_selected(),
           bg="#c0392b", fg="white", padx=10, pady=5).grid(row=0, column=3)

    # Table Frame
    table_frame = Frame(alert_frame)
    table_frame.grid(row=2, column=0, columnspan=3, sticky="nsew")

    alert_frame.grid_rowconfigure(2, weight=1)
    alert_frame.grid_columnconfigure(0, weight=1)

    # Style for bigger, grey-colored headers with light grey background
    style = ttk.Style()
    style.configure("Treeview.Heading",
                    font=("Segoe UI", 11, "bold"),
                    background="#dcdde1",
                    foreground="black",
                    relief="flat")
    style.map("Treeview.Heading", background=[('active', 'black')])

    cols = ("Product ID", "Name", "Quantity", "Expiry Date", "Status")
    tree = ttk.Treeview(table_frame, columns=cols, show="headings", style="Treeview")
    tree.grid(row=0, column=0, sticky="nsew")

    scrollbar = Scrollbar(table_frame, orient=VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky="ns")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")

    tree.tag_configure("expired", background="#ffcccc")

    def get_filtered_items():
        inventory = load_inventory()
        today = datetime.now().date()
        days = 7 if filter_option.get() == "7 Days" else 30

        filtered = []
        for item in inventory:
            expiry_str = item.get("expiry_date", item.get("expiry", ""))
            try:
                expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            except:
                continue

            if filter_option.get() == "Expired" and expiry < today:
                status = "Expired"
            elif today <= expiry <= today + timedelta(days=days):
                status = "Expiring Soon"
            else:
                continue

            filtered.append({
                "product_id": item.get("product_id"),
                "name": item.get("name"),
                "quantity": item.get("quantity"),
                "expiry_date": expiry_str,
                "status": status
            })
        return sorted(filtered, key=lambda x: x["expiry_date"])

    def refresh_table():
        for i in tree.get_children():
            tree.delete(i)

        data = get_filtered_items()
        for row in data:
            tag = "expired" if row["status"] == "Expired" else ""
            tree.insert("", END, values=(
                row["product_id"],
                row["name"],
                row["quantity"],
                row["expiry_date"],
                row["status"]
            ), tags=(tag,))

    def archive_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select expired item(s) to delete.")
            return

        names = [tree.item(i)['values'][1] for i in selected]
        item_list = "\n".join(names)
        confirm = messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove the following item(s)?\n\n{item_list}")
        if not confirm:
            return

        inventory = load_inventory()
        selected_ids = [tree.item(i)['values'][0] for i in selected]
        new_inventory = [item for item in inventory if item.get("product_id") not in selected_ids]
        save_inventory(new_inventory)
        refresh_table()
        messagebox.showinfo("Removed", "Selected items have been removed from inventory.")

    filter_option.trace_add("write", lambda *args: refresh_table())

    refresh_table()
    return alert_frame