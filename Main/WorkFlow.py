import codecs
import os
import random
import time
from collections import defaultdict
import numpy as np
import Clustering
import Evaluate
import got3
import Information
import OpinionMining
import Claim
import Twitter
import Utility
from chowmein import label_topic
from gensim.models.word2vec import LineSentence, Word2Vec
from pathlib import Path


class WorkFlow(object):
    """The workfolw of the system."""

    def __init__(self, rootpath, folderpath):
        """Initialize the parameters.

        Parameters
        ----------
        rootpath : str
            the root path of the data
        folderpath : str
            the fodler path of the data

        Returns
        -------
        None

        """
        self.rootpath = rootpath
        self.folderpath = folderpath
        self.helper = Utility.Helper(rootpath)
        self.preprocessData = Utility.PreprocessData(rootpath)
        self.getSimilarity = None

    def getTweets(self, query, start, end):
        """Get the the final tweets.

        Returns
        -------
        None

        """
        gettweets = Twitter.GetTweets(self.rootpath, self.folderpath,
                                      start, end, query)
        gettweets.start_getTweets()

    def getClaims(self, query):
        """Get claims.

        Arguments:
            query {str} -- the initial query
        """
        # folderPath = os.path.join(folderpath, 'final')
        # fullPath = os.path.join(self.rootpath, folderPath)
        self.preprocessData.generateTweetsLines(self.folderpath)

        claimExtractor = Claim.ClaimExtractor(self.rootpath, self.folderpath)

        tweets_list = list(self.helper.getTweet(self.folderpath))
        cleanedTweets = []
        for tweet in tweets_list:
            c1 = self.preprocessData.cleanTweet(tweet.text)
            cleanedTweets.append(c1)
        print("Parsing...")
        mergedNoun, sortedSubject2Number, \
            subject2tweetInfo, parsedTweets = claimExtractor.collectSubject(
                tweets_list, cleanedTweets)
        # sortedSubject2Number = self.helper.loadJson(
        #     os.path.join(self.folderpath, "final", "sorted_subject2number.json"))
        # subject2tweetInfo = self.helper.loadJson(
        #     os.path.join(self.folderpath, "final", "subject2tweetInfo.json"))
        # parsedTweets = self.helper.loadJson(
        #     os.path.join(self.folderpath, "final", "tweets_id2Info.json"))
        candidateClaimsMergedClause, \
            candidateFullClaimsMergedClause = claimExtractor.getCandidateClaims(
                tweets_list, mergedNoun, sortedSubject2Number, subject2tweetInfo,
                parsedTweets, query[1:])

        return candidateClaimsMergedClause, candidateFullClaimsMergedClause
        # mergedCandidateClaims = claimExtractor.mergeSimilarSubjects(
        #     candidateClaims)

    def getClusterClaims(self, query, eps):
        claims, fullClaims = self.getClaims(query)
        # filePath = os.path.join(self.folderpath, "final",
        #                         "candidateClaimsMergedClause.json")
        # print("filePath ", filePath)
        # claims = self.helper.loadJson(filePath)

        # filePath = os.path.join(self.folderpath, "final",
        #                         "candidateFullClaimsMergedClause.json")
        # print("filePath ", filePath)
        # fullClaims = self.helper.loadJson(filePath)

        skipthoughts_model = {"name": "skipthoughts",
                              "modelPath": self.rootpath + "/.." +
                              "/skip_thoughts/pretrained/skip_thoughts_uni_2017_02_02/exp_vocab",
                              "checkpointPath": "model.ckpt-501424"}
        sent2vec_model = {"name": "sent2vec",
                          "modelPath": "/lustre/scratch/haoxu/twitter_bigrams.bin"}

        self.getSimilarity = Claim.GetSimilarity(
            self.rootpath,
            self.folderpath,
            skipthoughts_model)
        tweets_list = list(self.helper.getTweet(self.folderpath))
        cluster2claimsIndexes, cluster2coreSampleIndices = self.getSimilarity.getClusteredClaims(
            claims, tweets_list, eps)
        return cluster2claimsIndexes, cluster2coreSampleIndices, claims, fullClaims

    def getClusterRankClaims(self, query, eps):
        cluster2claimsIndexes, cluster2coreSampleIndices, \
            claims, fullClaims = self.getClusterClaims(
                query, eps)
        getSimilarity = Claim.GetSimilarity(
            self.rootpath,
            self.folderpath)
        tweets_list = list(self.helper.getTweet(self.folderpath))
        rankedClusterClaims = getSimilarity.rankClusteredClaims(
            cluster2claimsIndexes, cluster2coreSampleIndices, claims, fullClaims, tweets_list)
        return rankedClusterClaims

        """similarClaimsComponents, sortedSimilarClaims = getSimilarity.getSimilarClaims(
            candidateClaimsMergedClause, tweets_list)
        self.helper.dumpJson(self.folderpath+"/final",
                             "similar_claims_components.json",
                             similarClaimsComponents)
        print("similar_claims_components.json has been saved.")
        self.helper.dumpJson(self.folderpath+"/final",
                             "ranked_similar_claims.json",
                             sortedSimilarClaims)
        print("ranked_similar_claims.json has been saved.")"""

        # claimExtractor.rankClaims(
        #     query[1:], tweets_list, similarClaimsComponents)

    def getNews(self, folderpath, top=5):
        event2timeScope = {
            "Gabapentin_0628_0121": ["2017-06-28T00:00:00Z", "2018-01-21T00:00:00Z"],
            "SanctuaryCities_0516_0523": ["2018-05-16T00:00:00Z", "2018-05-23T00:00:00Z"],
            "WhereAreTheChildren_0418_0527": ["2018-04-18T00:00:00Z", "2018-05-27T00:00:00Z"],
            "Ingraham_0618_0624": ["2018-06-18T00:00:00Z", "2018-06-24T00:00:00Z"],
            "ItsJustAJacket_0621_0624": ["2018-06-21T00:00:00Z", "2018-06-24T00:00:00Z"],
            "immigrants_0622_0624": ["2018-06-22T00:00:00Z", "2018-06-24T00:00:00Z"],
            "JetLi_0519_0523": ["2018-05-19T00:00:00Z", "2018-05-23T00:00:00Z"],
            "BandyLee_0110_0115": ["2018-01-10T00:00:00Z", "2018-01-15T00:00:00Z"],
            "JackBreuer_1228_0115": ["2017-12-28T00:00:00Z", "2018-01-15T00:00:00Z"],
            "SouthwestKey_0620_0624": ["2018-06-20T00:00:00Z", "2018-06-24T00:00:00Z"],
            "Capriccio_0516_0523_new": ["2018-05-16T00:00:00Z", "2018-05-23T00:00:00Z"]
        }
        if not self.getSimilarity:
            skipthoughts_model = {"name": "skipthoughts",
                                  "modelPath": self.rootpath + "/.." +
                                  "/skip_thoughts/pretrained/skip_thoughts_uni_2017_02_02/exp_vocab",
                                  "checkpointPath": "model.ckpt-501424"}
            sent2vec_model = {"name": "sent2vec",
                              "modelPath": "/lustre/scratch/haoxu/twitter_bigrams.bin"}
            self.getSimilarity = Claim.GetSimilarity(
                self.rootpath,
                self.folderpath,
                skipthoughts_model)

        folderPath = os.path.join(self.folderpath, "final")
        rankedClusterClaims = self.helper.loadJson(
            folderPath+"/ranked_cluster_claims.json")
        count = 0
        for index, info in enumerate(rankedClusterClaims):
            if count >= top:
                continue
            count += 1
            query = info[0]
            start = event2timeScope[folderpath][0]
            end = event2timeScope[folderpath][1]

            # find similar news
            alylienNewsAPI = Information.AylienNewsAPI()
            news = alylienNewsAPI.getNews(query, start, end, 10)
            if len(news) == 0:
                print("no news.")
                print("folder ", folderpath)
                print("info ", info)
                continue
            titles = alylienNewsAPI.getTitles(news)
            # find final news based the most similar news
            query = self.getSimilarity.getSimilarNews(query, titles)
            finalNews = alylienNewsAPI.getNews(query, start, end, 10)
            self.helper.dumpPickle(
                folderPath+"/news_bk", str(index)+"_news.pickle", finalNews)
            finalNewsDict = [i.to_dict() for i in finalNews]
            self.helper.dumpJson(folderPath+"/news",
                                 str(index)+"_news.json", finalNewsDict)
            print("{}th claim: news has been saved.".format(index))
            
            # sentiment = alylienNewsAPI.getSentiment(finalNews)
            # sentiments[index] = sentiment
        # self.helper.dumpJson(
        #     folderPath,
        #     "representative_claims_to_news_sentiments.json",
        #     sentiments)
        # print("representative_claims_to_news_sentiments.json has been saved.")

    def getSimilarTweets4Claim(self):
        # get claims
        claims = list(self.helper.getClaim(self.folderpath))
        # lowercase
        # claims = [claim.lower() for claim in claims]
        # get tweets
        tweets = self.helper.getTweet(self.folderpath)
        cleanedTweets = []
        for tweet in tweets:
            # tweets_list.append(tweet)
            c1 = self.preprocessData.cleanTweet(tweet.text)
            cleanedTweets.append(c1)
        getSimilarity = Claim.GetSimilarity(
            "/home/hao/Workplace/HaoXu/Data/skip_thoughts/pretrained/skip_thoughts_uni_2017_02_02/exp_vocab",
            "model.ckpt-501424")

        sentences, tweetIndex = getSimilarity.splitSentences(
            cleanedTweets)
        encodedSentences = getSimilarity.encodeSen(sentences)

        # for index, claim in enumerate(claims):
        encodedClaims = getSimilarity.encodeSen(claims)
        claims2tweets = getSimilarity.getTweets4Claims(
            sentences, encodedSentences, claims, encodedClaims, tweetIndex)

        for claimID, sentInfos in claims2tweets.items():
            claims2tweets[claimID] = self.preprocessData.sortListofLists(
                sentInfos, False)
        self.helper.dumpJson(
            self.folderpath, "final/sorted_claims2tweets.json", claims2tweets)
        print("sorted_claims2tweets.json have been saved.")

    def getQuery(self, folderpath):
        """Get query for svo of each cluster.

        Save the subject2queries.json for each cluster
        Returns
        -------
        None

        """
        queryGenerator = Information.QueryGenerator(self.rootpath)
        print("Getting query for {}".format(folderpath))
        queryGenerator.generateQuery(folderpath)

    def getSnippets(self, folderpath):
        """Get the google search snippets.

        Parameters
        ----------
        fullPath : str
            full path of folder

        Returns
        -------
        None

        """
        print("Getting snippets for {}".format(folderpath))
        # s2q = self.helper.loadJson(os.path.join(folderpath, 'final',
        #                                         'subject2svoqueries.json'))
        queries = self.helper.loadCsv(
            folderpath+"/final", "candidate_queries.csv")
        fullPath = os.path.join(self.rootpath, folderpath)

        relevant = []
        for idx, query in enumerate(queries):
            print("Crawling query {} ...".format(query[1]))
            googleSnippets = Information.GoogleSnippets(fullPath, query[0],
                                                        idx, query[1])
            res = googleSnippets.start_crawl()
            relevant.append(res)
            time.sleep(random.randint(1, 11))
        # for topic in s2q:
        #     relevant = []
        #     for idx, t in enumerate(s2q[topic]):
        #         # print("Searching for topic {} with query {}".format(topic,
        #         #                                                     query))
        #         googleSnippets = Information.GoogleSnippets(fullPath, topic,
        #                                                     idx, t['query'])
        #         res = googleSnippets.start_crawl()
        #         relevant.append(res)
        #         time.sleep(random.randint(1, 11))
        output_root = os.path.join(folderpath, 'final')
        self.helper.dumpJson(output_root, "snippets.json", relevant)
        # output_root = os.path.join(folderpath, 'final', 'snippets')
        # if not os.path.exists(output_root):
        # os.makedirs(output_root)
        # self.helper.dumpJson(output_root, "snippets.json", total_snippets)

    def getOpinion(self, folderpath):
        """Get the opinion for each cluster.

        Parameters
        ----------
        folderpath : str
            the folder path of the data

        Returns
        -------
        list
            [
                {"text": ..., "id": ..., "polarity": ...},
                {"text": ..., "id": ..., "polarity": ...}
            ]

        """
        sentiment140 = OpinionMining.Sentiment140API()

        folderPath = os.path.join(self.rootpath, folderpath, 'final',
                                  'snippets')
        svoQuery = self.helper.loadJson(os.path.join(self.rootpath, folderpath,
                                                     'final', 'subject2svoqueries.json'))
        subjectFolderPaths = os.listdir(folderPath)
        for subjectFolderPath in subjectFolderPaths:
            svos = [sq['svo'] for sq in svoQuery[subjectFolderPath]]
            filenames = os.listdir(os.path.join(folderPath, subjectFolderPath))
            data4svos = []
            for filename in filenames:
                # get opinion for svo
                idx = int(filename[0])
                data4svos.append({'text': svos[idx],
                                  'id': idx})
                # get opinions for snippets
                fullPath = os.path.join(folderPath, subjectFolderPath, filename
                                        )
                snippets = self.helper.loadJson(fullPath)
                data4snippets = []
                for snippet in snippets:
                    data4snippets.append({'text': snippet['snippets'],
                                          'id': int(snippet['id'][-1])})
                result4snippets = sentiment140.bulk_classify_json(
                    data4snippets)
                self.helper.dumpJson(os.path.join(folderPath,
                                                  subjectFolderPath),
                                     filename[:-5] + '_opinion.json',
                                     result4snippets)
            result4svo = sentiment140.bulk_classify_json(data4svos)
            self.helper.dumpJson(os.path.join(folderPath,
                                              subjectFolderPath),
                                 'svos_opinion.json', result4svo)
            print("opinions for {} have been saved.".format(subjectFolderPath))

    def getCorpus4Classification(self, folderpath, top=5):
        """Get corpus as .csv file for further classification.        
        Arguments:
            folderpath {str} -- the path to data folder
            flag {str} -- 'event': get corpus for whole tweets.
                          'cluster': get corpus for each cluster.
        """

        folderPath = os.path.join(folderpath, 'final')
        rankedClusterClaims = self.helper.loadJson(
            folderPath+"/ranked_cluster_claims.json")
        representativeClaimToSubject = self.helper.loadJson(
            folderPath+"/representative_claim_to_subject.json")
        representativeClaimToFulClaimsCluster = self.helper.loadJson(
            folderPath+"/representative_claim_to_full_claims_cluster.json")
        count = 0
        for index, info in enumerate(rankedClusterClaims):
            if count >= top:
                break
            claim = info[0]
            subject = representativeClaimToSubject[claim]
            clusterClaims = representativeClaimToFulClaimsCluster[claim]
            self.preprocessData.getCorpus4CsvFromRepresentativeClaims(
                folderPath+"/corpus/"+str(index), index, subject, claim)
            self.preprocessData.getCorpus4CsvFromClusterClaims(
                folderPath+"/corpus/"+str(index), index, subject, clusterClaims)
            count += 1
            # self.preprocessData.getCorpus4csvFromSnippets(folderPath)

    def getSimilarity4Statements(self, folderpath):
        """Get similarity between candiadate statements and target statement."""
        getSimilarity = Evaluate.GetSimilarity('tfidf', self.rootpath)
        tokens_candidates, id2claims = getSimilarity.getCorpusOfCandidateClaims(
            folderpath)
        tokens_target = getSimilarity.getCorpusOfTargetClaim(folderpath)
        # print("tokens_statements", len(tokens_statements))
        # print("tokens_target", tokens_target)
        vectors_candidates = getSimilarity.getVector(tokens_candidates)
        vector_target = getSimilarity.getVector(tokens_target)
        # print("vectors_candidates", vectors_candidates[0:1].shape)
        # print("vector_target", vector_target.shape)
        similarities = getSimilarity.getCosineSimilarity(
            vectors_candidates, vector_target)
        # print(similarities, vectors_candidates)
        # print(similarities[0], len(similarities[0]))

        # average, max, min
        maximum = max(similarities[0])
        print("max: {}".format(maximum))

        id2similarities = dict(enumerate(list(similarities[0])))
        data = []
        for key in id2claims.keys():
            data.append([id2claims[key], id2similarities[key]])
        self.helper.dumpCsv(
            folderpath+"/final", "similarities.csv", ['statement', 'similarity'], data)

    def getSimilarityStatements2Tweets(self, folderpath):
        """Get similarity between candidate claims and tweets.

        Arguments:
            folderpath {str} -- the path to data folder

        Returns:
            None -- index_tweet_2_index_candidate_claim.json;
                    index_candidate_claim_2_index_tweet.json;
                    index_candidate_claim_2_tweet.json are generated.
        """
        getSimilarity = Evaluate.GetSimilarity('tfidf', self.rootpath)
        tokens_claims, id2claims = getSimilarity.getCorpusOfCandidateClaims(
            folderpath)
        print("length of statements ", len(tokens_claims))

        tokens_tweets, id2tweets = getSimilarity.getCorpusOfTweets(
            folderpath)
        print("length of tweets ", len(tokens_tweets))

        # return None if any of them is None
        if len(tokens_claims) == 0 or len(tokens_tweets) == 0:
            print("no statements or tweets.")
            return
        vectors_claims = getSimilarity.getVector(tokens_claims)
        print("shape of vectors_claims ", vectors_claims.shape)
        vector_tweets = getSimilarity.getVector(tokens_tweets)
        print("shape of vector_tweets ", vector_tweets.shape)

        # shape is #vector_tweets x #vectors_candidates
        similarities = getSimilarity.getCosineSimilarity(
            vectors_claims, vector_tweets)
        print("shape of similarities ", similarities.shape)

        # get max indices of candidates statement for each tweet
        index_tweet_2_max_index_candidate_claim = enumerate(
            list(np.argmax(similarities, axis=1)))
        self.helper.dumpJson(folderpath+"/final",
                             "index_tweet_2_index_candidate_claim.json",
                             index_tweet_2_max_index_candidate_claim)
        # reverse the key and value
        max_index_candidate_claim_2_index_tweet = defaultdict(list)
        for tid, sid in index_tweet_2_max_index_candidate_claim:
            max_index_candidate_claim_2_index_tweet[sid].append(tid)
        self.helper.dumpJson(folderpath+"/final",
                             "index_candidate_claim_2_index_tweet.json",
                             max_index_candidate_claim_2_index_tweet)
        # generate {index_claim: [tweet1, tweet2, ...]}
        index_candidate_claim_2_tweet = defaultdict(list)
        for index_candidate_claim in max_index_candidate_claim_2_index_tweet.keys():
            for index_tweet in max_index_candidate_claim_2_index_tweet[index_candidate_claim]:
                index_candidate_claim_2_tweet[index_candidate_claim].append(
                    id2tweets[index_tweet])
        self.helper.dumpJson(os.path.join(
            folderpath, "final"), "index_candidate_claim_2_tweet.json",
            index_candidate_claim_2_tweet)
        print("index_candidate_claim_2_tweet.json has been saved.")