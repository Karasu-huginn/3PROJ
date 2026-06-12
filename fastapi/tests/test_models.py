import models


def test_collections_has_is_default_column(db_session, user_one):
    """is_default persists and defaults to False."""
    default_list = models.Collections(user_id=user_one.id, name="En cours", is_default=True)
    custom_list = models.Collections(user_id=user_one.id, name="Perso")
    db_session.add_all([default_list, custom_list])
    db_session.commit()
    db_session.refresh(default_list)
    db_session.refresh(custom_list)
    assert default_list.is_default is True
    assert custom_list.is_default is False
