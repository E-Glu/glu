import MytestTestCardList from '@/components/mytest/mytestTestCardList';
import { getSolvedTypeTestAPI } from '@/utils/user/mytest';
import { ProblemType, SolvedProblemResponse } from '@/types/ProblemTypes';
import { GetServerSideProps } from 'next';
import { getCookie } from 'cookies-next';
import Head from 'next/head';
import styles from './mytest.module.css';

export const getServerSideProps: GetServerSideProps = async (context) => {
  const { req, res } = context;
  const accessToken = getCookie('accessToken', { req, res });

  if (!accessToken) {
    return {
      redirect: {
        destination: '/',
        permanent: false,
      },
    };
  }

  const problemData01 = await getSolvedTypeTestAPI(
    'PT01',
    0,
    undefined,
    undefined,
    true,
    undefined,
    context,
  );

  const problemData02 = await getSolvedTypeTestAPI(
    'PT02',
    0,
    undefined,
    undefined,
    true,
    undefined,
    context,
  );

  const problemData03 = await getSolvedTypeTestAPI(
    'PT03',
    0,
    undefined,
    undefined,
    true,
    undefined,
    context,
  );

  const testDataList = [
    {
      problemType: { code: 'PT01', name: '어휘 및 문법' },
      problemData: problemData01,
    },
    {
      problemType: { code: 'PT02', name: '독해' },
      problemData: problemData02,
    },
    {
      problemType: { code: 'PT03', name: '추론' },
      problemData: problemData03,
    },
  ];

  return {
    props: {
      testDataList,
    },
  };
};

interface MytestStarredPageProps {
  testDataList: [
    { problemType: ProblemType; problemData: SolvedProblemResponse },
  ];
}

export default function MytestStarredPage({
  testDataList,
}: MytestStarredPageProps) {
  return (
    <div className={styles.container}>
      <Head>
        <title>나의 학습 - 찜한 문제</title>
        <link rel="icon" type="image/png" sizes="48x48" href="/favicon.png" />
        <link rel="icon" type="image/x-icon" href="/favicon.ico" />
      </Head>
      {testDataList.map((testData) => (
        <MytestTestCardList
          key={testData.problemType.code}
          testData={testData?.problemData}
          problemType={testData?.problemType}
          pageType="starred"
        />
      ))}
    </div>
  );
}
