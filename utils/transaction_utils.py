# utils/transaction_utils.py


def classify_transaction_type(
    grantor_builder_id: int | None,
    grantee_builder_id: int | None,
    grantor_land_banker_id: int | None,
    grantee_land_banker_id: int | None,
) -> str:
    if grantor_builder_id is not None and grantee_builder_id is not None:
        return 'Builder to Builder'

    if grantee_builder_id is not None:
        return 'Builder Purchase'

    if grantee_land_banker_id is not None:
        return 'Land Banker Purchase'

    return 'House Sale'
