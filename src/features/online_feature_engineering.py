from src.features.feature_definitions import FeatureDefinitions

class OnlineFeatureEngineer:

    def compute(self, tx, state):

        user = state["user"]

        enriched = {}

        enriched.update(
            FeatureDefinitions.geo_features(
                tx,
                user
            )
        )

        enriched.update(
            FeatureDefinitions.identity_features(
                tx,
                user,
                state["known_device"],
                state["known_ip"]
            )
        )

        enriched.update(
            FeatureDefinitions.amount_features(
                tx,
                user,
                state["country"]
            )
        )

        enriched.update(
            FeatureDefinitions.behavioral_features(
                tx,
                state
            )
        )

        return enriched