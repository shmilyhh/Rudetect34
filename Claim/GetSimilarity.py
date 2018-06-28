import os
import numpy as np
import scipy.spatial.distance as sd
from skip_thoughts import configuration
from skip_thoughts import encoder_manager
from nltk import sent_tokenize
from nltk import word_tokenize
from collections import defaultdict
import Utility
from sklearn.cluster import DBSCAN


class GetSimilarity(object):
    """Get similar tweets for claim or claims based on sen2vec in skip thoughts model."""

    def __init__(self, modelPath, checkpointPath):
        """Initialize the TweetsExtractor4Claim model.

        Arguments:
            modelPath {str} -- the path to model folder
            checkpointPath {str} -- the filename of mode.ckpt-xxxx
        """
        self.modelPath = modelPath
        self.checkpointPath = os.path.join(modelPath, "..", checkpointPath)
        self.vocabFile = os.path.join(modelPath, "vocab.txt")
        self.embeddingMatrixFile = os.path.join(modelPath, "embeddings.npy")

        self.encoder = encoder_manager.EncoderManager()
        self.encoder.load_model(configuration.model_config(),
                                vocabulary_file=self.vocabFile,
                                embedding_matrix_file=self.embeddingMatrixFile,
                                checkpoint_path=self.checkpointPath)

    def splitSentences(self, cleanedTweets):
        """Split sentences in each tweet.

        Arguments:
            cleanedTweets {list} -- a list of cleaned tweets

        Returns:
            tuple -- (sentences, tweetIndices)
        """
        sentences = []
        tweetIndex = []
        for index, tweet in enumerate(cleanedTweets):
            sents = sent_tokenize(tweet)
            for sent in sents:
                if len(word_tokenize(sent)) >= 3:
                    sent = Utility.PreprocessData.removePunctuation(sent)
                    # sentences.append(sent.lower())
                    sentences.append(sent)
                    tweetIndex.append(index)
        return sentences, tweetIndex

    def encodeSen(self, sentences):
        """Encode the sentences based on the sent2vec model.

        Arguments:
            sentences {list} -- a list of sentences

        Returns:
            list -- a list of encoded sentences
        """

        encodedSentences = self.encoder.encode(sentences)

        return encodedSentences

    def getTweets4Claims(self, sentences, encodedSentences, claims, encodedClaims, tweetIndex, num=10):
        """Get tweets for claim.

        Arguments:
            sentences {list} -- a list of sentences
            encodedSentences {np.array} -- a list of encoded sentences
            claims {list} -- a list of claims
            encodedClaims {np.array} -- a list of encoded claims
            tweetIndex {list} -- the corresponding tweet index

        Keyword Arguments:
            num {int} -- the number of top N (default: {10})

        Returns:
            defaultdict(list) -- {claimID: [sentence, score, tweetIndex]}
        """

        claims2tweets = defaultdict(list)
        scores = sd.cdist(encodedSentences, encodedClaims, "cosine")
        # sorted_ids = np.argsort(scores)
        maxClaimIDs = np.argmin(scores, axis=1)
        for index, maxClaimID in enumerate(maxClaimIDs):
            claims2tweets[np.asscalar(maxClaimID)].append(
                (sentences[index],
                 scores[index][np.asscalar(maxClaimID)],
                 tweetIndex[index]))
        # for claimID, sentInfos in claims2tweets.items():
        #     print("Sentence:")
        #     print("", claims[claimID])
        #     print("\nNearest neighbors:")
        #     for sent, score, twIndx in sentInfos:
        #         print(" %s (%.3f) %d" %
        #               (sent, score, twIndx))
        return claims2tweets

    def getSimilarClaims(self, claims, tweets):
        """Get similar claims.

        Arguments:
            claims {list} -- [[tweetID, subjectID, afterSubjectIdx, claim1], ...]
            tweets {list} -- a list of tweets

        Returns:
            list -- [claim1, claim2, ...]
        """
        # tweetID_675 = None
        # tweetID_14 = None
        # tweetID_956 = None
        # for index, item in enumerate(claims):
        #     if item[0] == 675:
        #         print("index of tweetID 675 ", index)
        #         tweetID_675 = index
        #     if item[0] == 14:
        #         print("index of tweetID 14 ", index)
        #         tweetID_14 = index
        #     if item[0] == 956:
        #         print("index of tweetID 956 ", index)
        #         tweetID_956 = index
        #     if tweetID_675 and tweetID_14 and tweetID_956:
        #         break

        claimsContent = [claim[3] for claim in claims]
        # encodedClaims = [self.encodeSen([cc]) for cc in claimsContent]
        # encodedClaims_numpy = np.concatenate(encodedClaims)
        encodedClaims = self.encodeSen(claimsContent)

        # scores = sd.cdist(encodedClaims_numpy, encodedClaims_numpy, "cosine")
        scores = sd.cdist(encodedClaims, encodedClaims, "cosine")
        similarClaimsIndeices = np.argwhere(scores < 0.5)

        # test = [claimsContent[tweetID_675],
        #         claimsContent[tweetID_14], claimsContent[tweetID_956]]
        # encodedtest = self.encodeSen(test)
        # scores_test = sd.cdist(encodedtest, encodedtest, "cosine")
        # print("test ", scores_test)

        # print(encodedtest[0])
        # print(encodedClaims[tweetID_675])

        # print("657 ", np.array_equal(
        #     encodedtest[0], encodedClaims[tweetID_675]))
        # print("14 ", np.array_equal(encodedtest[1], encodedClaims[tweetID_14]))
        # print("956 ", np.array_equal(
        #     encodedtest[2], encodedClaims[tweetID_956]))

        # print("tweetID_675: claims index {} {}".format(
        #     tweetID_675, claimsContent[tweetID_675]))
        # print("pair indexes lower than 0.5 {}".format(
        #     np.argwhere(scores[tweetID_675] < 0.5).tolist()))

        # tmp_675 = np.argwhere(scores[tweetID_675] < 0.5).tolist()
        # print("original claim {}".format(claimsContent[tweetID_675]))
        # for t in tmp_675:
        #     print("claim {} score {}".format(
        #         claimsContent[t[0]], scores[tweetID_675][t[0]]))

        # print("tweetID_14: claims index {} {}".format(
        #     tweetID_14, claimsContent[tweetID_14]))
        # print("pair indexes lower than 0.5 {}".format(
        #     np.argwhere(scores[tweetID_14] < 0.5).tolist()))

        # tmp_14 = np.argwhere(scores[tweetID_14] < 0.5).tolist()
        # print("original claim {}".format(claimsContent[tweetID_14]))
        # for t in tmp_14:
        #     print("claim {} score {}".format(
        #         claimsContent[t[0]], scores[tweetID_14][t[0]]))

        similarClaimsIndeicesComponents = Utility.Helper.getConnectedComponents(
            similarClaimsIndeices.tolist())
        similarClaimsComponents = defaultdict(list)
        similarClaims = defaultdict(int)
        for component in similarClaimsIndeicesComponents:
            tweet2features = defaultdict(int)
            for index in component:
                tweetID = claims[index][0]
                text = claims[index][3]
                features = tweets[tweetID].reply + \
                    tweets[tweetID].retweets + \
                    tweets[tweetID].favorites + 1
                tweet2features[text] += features
            sortedTweet2Number = Utility.PreprocessData.sortDict(
                tweet2features)
            similarClaimsComponents[sortedTweet2Number[0][0]] = list(component)
            componentFeatures = [feature for text,
                                 feature in sortedTweet2Number]
            similarClaims[sortedTweet2Number[0][0]] = sum(
                componentFeatures) / len(componentFeatures)
        sortedSimilarClaims = Utility.PreprocessData.sortDict(
            similarClaims)
        return similarClaimsComponents, sortedSimilarClaims

    def getClusteredClaims(self, claims, tweets):
        """Get clusters of the claims by DBSCAN.

        Arguments:
            claims {list} -- [[tweetID, subjectID, afterSubjectIdx, claim1], ...]
            tweets {list} -- a list of tweets

        Returns:
            dict -- {cluster1: [claim1, ...], ...}
        """
        cluster2claims = defaultdict(list)
        claimsContent = [claim[3] for claim in claims]
        encodedClaims = self.encodeSen(claimsContent)
        scores = sd.cdist(encodedClaims, encodedClaims, "cosine")

        db = DBSCAN(eps=0.35, min_samples=2, metric="precomputed").fit(scores)
        labels = db.labels_

        for index, label in enumerate(labels):
            if label == -1:
                continue
            cluster2claims[label].append(index)

        for key, value in cluster2claims.items():
            print("=" * 100)
            print("cluster {}".format(key))
            for v in value:
                print(claimsContent[v])
        return cluster2claims
