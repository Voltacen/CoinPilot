import csv
import io

from flask import Response, jsonify


class WithdrawalPolicy:
    @staticmethod
    def allow_withdrawal(asset_type: str = "platform_credit") -> bool:
        """CoinPilot credits are intentionally non-withdrawable."""
        return False

    @staticmethod
    def withdrawal_error_response():
        return jsonify({
            "error": "Withdrawal is disabled: CoinPilot credits are non-withdrawable platform balances.",
            "status": "locked",
            "asset_type": "platform_credit",
        }), 403

    @staticmethod
    def csv_export_response(rows, filename="coinpilot_ledger_history.csv"):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["created_at", "entry_type", "amount", "direction", "reference_note", "source_account_id", "destination_account_id"])

        for row in rows:
            direction = "outgoing" if row.source_account_id else "incoming"
            writer.writerow([
                row.created_at.isoformat() if getattr(row, "created_at", None) else "",
                row.entry_type,
                str(row.amount),
                direction,
                row.reference_note or "",
                row.source_account_id or "",
                row.destination_account_id or "",
            ])

        response = Response(output.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
